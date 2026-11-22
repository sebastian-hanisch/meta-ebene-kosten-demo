"""Baut data/mek_karte.json (die Karte: wo lohnt es, wo nicht) und data/mek_kosten.json (das Kostenbuch).

    python tools/mek_make_karte.py            schreibt beide Dateien aus mek_h5.json, mek_gegner.json und den Dateien der Nachbardemos (falls vorhanden)
    python tools/mek_make_karte.py --check    zählt jede Zeile der Karte aus den Quellen nach und meldet Abweichungen

Jede Zeile der Karte ist eine Zählung aus einer Messung, mit Zähleinheit, Entscheidungsregel, Voraussetzung und Quelle; eine Zeile ohne Zahl heißt „nicht gemessen“.
Die Linie hat zwei Entscheidungsregeln (Einplanung: Regel D1; Packen: Median und Läufe), eine Zählung mischt nie beide.
Quellen der Nachbarstücke (nur gelesen, fehlt eine Datei, entfallen ihre Zeilen): auswahlregeln-demo/asw_frozen.json (Stück 3), zugmenge-demo/zgm_band.json (Stück 2),
regel-verteilungswechsel-demo/rvw_tabellen.json (Stück 7), heuristik-variation-demo/hva_precomputed.json (Stück 8)."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJEKTE = ROOT.parent
sys.path.insert(0, str(ROOT))

import mek_constants as C  # noqa: E402
import mek_frozen as F  # noqa: E402
from mek_stats import mittel, packen_urteil, zaehle  # noqa: E402

DATUM = "2026-11-21"
N_KARTE = 30
STUECKE = {1: "Heuristiken auswählen statt Lösungen", 2: "Die Zugmenge entscheidet", 3: "Wer belohnt wen?", 4: "Akzeptanz mal Auswahl",
           5: "Prioritätsregeln erzeugen", 6: "Platzierungsfunktionen erzeugen", 7: "Auf fremden Instanzen", 8: "Heuristiken variieren und bündeln",
           9: "Lohnt die Meta-Ebene?"}
EINHEIT = {"Rundtour": "Auswertung = bewerteter Kandidat", "Einplanung": "Auswertung = Regel auf 20 Trainingsinstanzen",
           "Bin Packing": "Auswertung = Regel auf 20 Trainingsinstanzen; Einsatz in Läufen je Instanz"}
REGEL_STERN = "Break-even: N* ≤ 30 in allen Wiederholungen"
REGEL_ZELLE = "Zellenmittel: Unterschied ≥ 0,25 Prozentpunkte (Marke aus Stück 1, ohne Intervall)"
REGEL_D1 = "D1 (Einplanung): Anteil ≥ 0,75 der Läufe, Median ≤ 1 Prozentpunkt, Wilcoxon p < 0,01"
REGEL_PACKEN = "Packen: Median ≤ −0,2 Prozentpunkte und in mindestens 15 von 20 Läufen < 0"


def zeile(zid, meta, gegner, fahrzeug, bedingung, art, regel, kosten, voraussetzung, stueck, quelle, **zahlen):
    z = dict(id=zid, meta_ebene=meta, gegner=gegner, fahrzeug=fahrzeug, einheit=EINHEIT[fahrzeug], bedingung=bedingung, art=art, regel=regel, kosten=kosten,
             voraussetzung=voraussetzung, stueck=stueck, stueck_name=STUECKE[stueck], quelle=quelle, datum=DATUM, stabil=True)
    z.update(zahlen)
    return z


def nicht_gemessen(zid, meta, gegner, fahrzeug, bedingung, warum, stueck=9):
    return zeile(zid, meta, gegner, fahrzeug, bedingung, "nicht_gemessen", "—", "—", warum, stueck, "nicht gemessen")


def _laden(pfad: Path):
    return json.loads(pfad.read_text(encoding="utf-8")) if pfad.exists() else None


# ------------------------------------------------------------------ Rundtour: eigene Messung H5
def rundtour_offline():
    rows = []
    for akz in C.H5_AKZ:
        for stufe in C.STUFEN:
            for art, k in (("mix", 1), ("mix", 3), ("mix", 10), ("einzel", 3)):
                z = F.zaehlung_lohnt(akz, "alle sechs", art, k, stufe, N_KARTE)
                lo = {"mix": "K·ℓ", "einzel": "8·K·ℓ"}[art]
                rows.append(zeile(
                    f"rt-offline-{akz}-{stufe}-{art}{k}", C.ARTEN_ANZEIGE[art] + f" (K = {k})", "Zufallsauswahl über alle acht Zugarten", "Rundtour",
                    f"{C.AKZ_ANZEIGE[akz]}, Einsatz {C.STUFEN_ANZEIGE[stufe]}, N = {N_KARTE}", "lohnt", REGEL_STERN,
                    f"E = {lo} mit ℓ = 50·n Auswertungen je Trainingsinstanz; Einsatz {'ℓ' if stufe == 'lo' else '4 ℓ'} je Instanz",
                    "6 Zellen (gleichverteilt, Gruppen, Gitter × n = 30, 60), 30 Testinstanzen × 5 Läufe, 5 Wiederholungen des Trainings; Instanzen aus derselben Verteilung wie das Training",
                    9, "mek_h5.json, Messung dieses Stücks", k=z["lohnt"], m=z["zellen"], k_mittel=z["mittel"], gewinn=round(z["gewinn"], 3), stabil=z["lohnt"] == z["mittel"]))
    return rows


def _zellen_je_instanz(liste, instanzen):
    """Mittel je Zelle (Familie, n) einer Liste je Instanz (Reihenfolge der Tripel `instanzen`)."""
    sums = {}
    for v, (f, n, _) in zip(liste, instanzen):
        sums.setdefault((f, n), []).append(v)
    return [mittel(sums[z]) for z in C.H5_ZELLEN]


def _bgs(differenzen, marke=C.MARKE_GEWINN):
    """(besser, gleich, schlechter) aus Zellenmitteln: ≥ +Marke besser, ≤ −Marke schlechter."""
    b = sum(d >= marke - 1e-12 for d in differenzen)
    s = sum(d <= -marke + 1e-12 for d in differenzen)
    return b, len(differenzen) - b - s, s


def rundtour_online():
    asw = _laden(PROJEKTE / "auswahlregeln-demo" / "asw_frozen.json")
    if asw is None:
        return []
    rows = []
    inst = [tuple(x) for x in asw["instanzen"]]
    namen = {"cf": "Choice Function", "laut": "Lernautomat", "q": "Q-Lernen"}
    for regel in ("cf", "laut", "q"):
        for akz in ("ob", "rr", "la"):
            for j, stufe in enumerate(("klein", "gross")):
                rand = [z[j] for z in asw["gap"]["voll"][akz]["rand/r2"]]
                lern = [z[j] for z in asw["gap"]["voll"][akz][f"{regel}/r2"]]
                d = _zellen_je_instanz([a - b for a, b in zip(rand, lern)], inst)
                b, g, s = _bgs(d)
                akz_name = {"ob": "nur besser", "rr": "Rekord-zu-Rekord", "la": "Late Acceptance (L = 50)"}[akz]
                rows.append(zeile(
                    f"rt-online-{regel}-{akz}-{stufe}", f"online gelernt: {namen[regel]}", "Zufallsauswahl", "Rundtour",
                    f"{akz_name}, Einsatz {'50·n' if j == 0 else '200·n'} Auswertungen", "bgs", REGEL_ZELLE,
                    "E = 0 (die Kosten des Lernens stehen im Einsatz)", "6 Zellen à 20 Instanzen × 3 Läufe, Standardbelohnung, ganze Menge der acht Zugarten", 3,
                    "auswahlregeln-demo/asw_frozen.json", b=b, g=g, s=s, m=6, mittel=round(mittel(d), 3)))
    return rows


def rundtour_menge():
    zgm = _laden(PROJEKTE / "zugmenge-demo" / "zgm_band.json")
    if zgm is None:
        return []
    inst = [tuple(x) for x in zgm["instanzen"]]
    rows = []
    for akz in ("ob", "rr", "la"):
        for j, stufe in enumerate(("klein (50·n)", "mittel (150·n)", "groß (400·n)")):
            voll = [z[j] for z in zgm["gap"][akz]["voll"]["rand"]]
            t3 = [z[j] for z in zgm["gap"][akz]["T3"]["rand"]]
            d = _zellen_je_instanz([a - b for a, b in zip(voll, t3)], inst)
            b, g, s = _bgs(d)
            akz_name = {"ob": "nur besser", "rr": "Rekord-zu-Rekord", "la": "Late Acceptance (L = 50)"}[akz]
            rows.append(zeile(
                f"rt-t3-{akz}-{j}", "feste Teilmenge T3 = {2opt, 2opt_lokal, 2opt_b5}, gleichverteilt (nachträglich gewählt)", "Zufallsauswahl über alle acht Zugarten", "Rundtour",
                f"{akz_name}, Einsatz {stufe}", "bgs", REGEL_ZELLE, "E = 0; die Wahl der Menge war nicht umsonst (nach Ansicht der Ergebnisse getroffen, die Kosten der Erkenntnis stehen nicht in der Bilanz)",
                "6 Zellen à 20 Instanzen × 3 Läufe; die Zahl führt Stück 2", 2, "zugmenge-demo/zgm_band.json", b=b, g=g, s=s, m=6, mittel=round(mittel(d), 3)))
    return rows


# ------------------------------------------------------------------ Einplanung
def einplanung_zeilen():
    rows = []
    gp_kosten = lambda b, g: f"E = {b} Auswertungen (GP) gegen {g} (ATC(k)): das {b / g:.1f}-Fache; Einsatz 1 Regel je Instanz"
    for g in C.EP_RASTER:
        for b in C.EP_B:
            bb, gg, ss = F.ep_zaehlung("gp", b, g)
            rows.append(zeile(f"ep-gp-atc{g}-{b}", f"Genetische Programmierung (GP), {b} Auswertungen", f"ATC(k), k aus {g} Werten", "Einplanung",
                              f"Suche mit {b} Auswertungen, Gegner mit {g} Auswertungen", "bgs", REGEL_D1, gp_kosten(b, g),
                              "8 Zellen (Regime klein und groß × Familien E, M, W, S), 20 Läufe je Zelle, Test auf der eigenen Zelle; eigene Umsetzung", 5,
                              "mek_gegner.json (ATC(g) neu gerechnet, GP-Läufe aus Stück 5)", b=bb, g=gg, s=ss, m=F.ep_zellen_gemessen("gp", b)))
    for b in C.EP_B:
        bb, gg, ss = F.ep_gegen_fest(b)
        rows.append(zeile(f"ep-gp-fest-{b}", f"Genetische Programmierung (GP), {b} Auswertungen", "beste der vier festen Regeln (SPT, EDD, WSPT, MDD)", "Einplanung",
                          f"Suche mit {b} Auswertungen", "bgs", REGEL_D1, f"E = {b} Auswertungen gegen 0 (feste Regel ohne Einstellung)",
                          "8 Zellen, 20 Läufe; der Regret wird gegen den schwachen Gegner geschlagen, nicht gegen ATC(k)", 5, "mek_gegner.json", b=bb, g=gg, s=ss, m=8))
    for variante, name in (("gp_impf", "GP mit ATC als Startbaum"), ("ones", "(1+1)-Suche über Bäume"), ("zufall", "Zufallssuche über Bäume")):
        for b in (16000,):
            bb, gg, ss = F.ep_zaehlung(variante, b, 11)
            m = F.ep_zellen_gemessen(variante, b)
            if m:
                rows.append(zeile(f"ep-{variante}-atc11-{b}", f"{name}, {b} Auswertungen", "ATC(k), k aus 11 Werten", "Einplanung", f"Suche mit {b} Auswertungen", "bgs", REGEL_D1,
                                  f"E = {b} Auswertungen gegen 11", f"{m} Zellen, 20 Läufe", 5, "mek_gegner.json", b=bb, g=gg, s=ss, m=m))
    return rows


def verteilungswechsel():
    t = _laden(PROJEKTE / "regel-verteilungswechsel-demo" / "rvw_tabellen.json")
    if t is None:
        return []
    rows = []
    for b in (16000, 4000, 1000):
        zs = [t["einplanung"]["familienwechsel"][r][str(b)] for r in ("klein", "gross")]
        bb, gg, ss = (sum(z[i] for z in zs) for i in range(3))
        rows.append(zeile(f"ep-wechsel-fam-{b}", f"GP, {b} Auswertungen, auf einer Familie trainiert", "ATC(k), auf der Trainingsfamilie eingestellt", "Einplanung",
                          "Familienwechsel: Test auf einer anderen Familie", "bgs", REGEL_D1, f"E = {b} Auswertungen, bei jedem Wechsel erneut",
                          "72 Zellen (2 Regime × 12 Trainings-Test-Paare × 3 Auftragszahlen), 20 Läufe; die Zählung führt Stück 7 (dieselben Läufe wie Stück 5)", 7,
                          "regel-verteilungswechsel-demo/rvw_tabellen.json", b=bb, g=gg, s=ss, m=bb + gg + ss))
    for regime in ("klein", "gross"):
        z = t["einplanung"]["n_wechsel_eigene_familie"][regime]["16000"]
        rows.append(zeile(f"ep-wechsel-n-{regime}", "GP, 16 000 Auswertungen, auf einem n trainiert", "ATC(k), auf dem Trainings-n eingestellt", "Einplanung",
                          f"Wechsel der Auftragszahl, eigene Familie, Regime {C.EP_REGIME_ANZEIGE[regime]}", "bgs", REGEL_D1, "E = 16 000 Auswertungen, bei jedem Wechsel erneut",
                          "8 Zellen, 20 Läufe; die Zählung führt Stück 7", 7, "regel-verteilungswechsel-demo/rvw_tabellen.json", b=z[0], g=z[1], s=z[2], m=sum(z)))
    return rows


# ------------------------------------------------------------------ Bin Packing
def bin_packing_zeilen():
    rows = []
    fam = C.BP_FAMILIEN
    for b in C.BP_BUDGETS:
        bb, gg, ss = F.bp_suche_zaehlung(b)
        m = bb + gg + ss
        rows.append(zeile(f"bp-suche-{b}", f"erzeugte Platzierungsregeln (7 Suchverfahren), {b} Auswertungen", "Best Fit", "Bin Packing", f"Suche mit {b} Auswertungen", "bgs", REGEL_PACKEN,
                          f"E = {b} Auswertungen gegen 0 (Best Fit); Einsatz 1 Lauf je Instanz", f"{m} Zellen (7 Verfahren × 3 Familien), 20 Läufe, Test 200 Instanzen, n = 60", 6,
                          "mek_gegner.json (Läufe aus Stück 6)", b=bb, g=gg, s=ss, m=m))
    for gitter in C.BP_PR2_GRID:
        u = zaehle(F.bp_pr2_urteil(f, gitter)["urteil"] for f in fam)
        rows.append(zeile(f"bp-pr2-{gitter}", f"PR2 mit {gitter} × {gitter} Gitter ({gitter * gitter} Auswertungen)", "Best Fit", "Bin Packing", "Zwei-Parameter-Regel, auf dem Training gewählt", "bgs",
                          REGEL_PACKEN, f"E = {gitter * gitter} Auswertungen gegen 0", "3 Zellen (Familien), 20 Läufe", 9, "mek_gegner.json (neu gerechnet)", b=u[0], g=u[1], s=u[2], m=3))
    hva = _laden(PROJEKTE / "heuristik-variation-demo" / "hva_precomputed.json")
    if hva is not None:
        for pool in ("Z-S", "EA-S", "GP-T"):
            for art, i, name in (("orakel", 0, "Orakelwahl (alle k Regeln laufen)"), ("merkmal", 1, "Merkmalswahl (ein Lauf je Instanz)")):
                u = []
                for f in fam:
                    d = [r["sets"]["greedy"]["3"]["T"]["same60"][i] for r in hva["m1"][f][pool]]
                    u.append(packen_urteil(d)["urteil"])
                b, g, s = zaehle(u)
                einsatz = "3 Läufe je Instanz" if art == "orakel" else "1 Lauf je Instanz"
                rows.append(zeile(f"bp-menge-{pool}-{art}", f"gierige Menge k = 3 aus dem Pool von {pool}, {name}", "Best Fit", "Bin Packing", "k = 3, Testmenge gleicher Familie", "bgs", REGEL_PACKEN,
                                  f"E = 1 000 Auswertungen; Einsatz {einsatz}", "3 Zellen (Familien), 20 Läufe; der Gewinn kommt aus Zusammenstellung und Orakelwahl, auch aus dem Zufallspool", 8,
                                  "heuristik-variation-demo/hva_precomputed.json", b=b, g=g, s=s, m=3))
        u = []
        for f in fam:
            d = [r["T"]["same60"][0] for r in hva["portfolio"][f]]
            u.append(packen_urteil(d)["urteil"])
        b, g, s = zaehle(u)
        rows.append(zeile("bp-portfolio", "Portfolio aus First Fit, Best Fit, Worst Fit mit Orakelwahl", "Best Fit", "Bin Packing", "3 bekannte Regeln", "bgs", REGEL_PACKEN, "E = 3 Auswertungen; Einsatz 3 Läufe je Instanz",
                          "3 Zellen, 20 Läufe", 8, "heuristik-variation-demo/hva_precomputed.json", b=b, g=g, s=s, m=3))
    return rows


def nicht_gemessen_zeilen():
    return [
        nicht_gemessen("ng-reserve", "zustandsabhängige Auswahl (Reserve R)", "feste Auswahl", "Rundtour", "Zustandsabhängigkeit", "nicht gemessen: keine zustandsabhängige Auswahl gerechnet"),
        nicht_gemessen("ng-la-laenge", "gelernte Auswahl, Late Acceptance mit anderer Listenlänge", "Zufallsauswahl", "Rundtour", "N* für L = 10", "nicht gemessen: N* nur für L = 50"),
        nicht_gemessen("ng-menge", "gelernte Auswahl bei einer Menge ohne dominante Zugart", "Zufallsauswahl", "Rundtour", "keine dominante Zugart", "nicht gemessen"),
        nicht_gemessen("ng-atc-n", "GP gegen ATC(k) mit je n eingestelltem k", "ATC(k)", "Einplanung", "k je Auftragszahl gewählt", "nicht gemessen"),
        nicht_gemessen("ng-bp-1000", "erzeugte Regeln mit mehr als 1 000 Auswertungen im Standard", "Best Fit", "Bin Packing", "Budgets über 1 000 (10 000 nur als Stichprobe in Stück 6 und 8)", "nicht als Zählung gemessen"),
        nicht_gemessen("ng-abstimmung", "Abstimmung der Meta-Ebene selbst (Lernraten, Populationsgrößen)", "Standardwerte", "Rundtour", "alle Meta-Ebenen mit Standardwerten gemessen", "nicht gemessen"),
        nicht_gemessen("ng-umrechnung", "Umrechnung der Auswertungen in Elementarschritte zwischen den Fahrzeugen", "—", "Rundtour", "Vergleich über Fahrzeuge", "nicht gemessen und nicht angeboten"),
    ]


def bauen_karte():
    zeilen = (rundtour_offline() + rundtour_online() + rundtour_menge() + einplanung_zeilen() + verteilungswechsel() + bin_packing_zeilen() + nicht_gemessen_zeilen())
    return dict(schema=1, datum=DATUM, hinweis="Zwei Entscheidungsregeln (Einplanung D1, Packen); eine Zählung mischt nie beide. Zahlen aus Messungen, keine Zeile sagt „lohnt nicht“ ohne Zahl.",
                zeilen=zeilen)


def bauen_kosten():
    """Zeilen des Kostenbuchs, die nicht aus der Wahl der Regler abhängen: Einheit, Gegner, Quelle (die Zahlen rechnet mek_evaluation live)."""
    return dict(schema=1, einheiten=EINHEIT, hinweis="Entwicklungskosten E und Einsatz b je Fahrzeug in dessen Einheit; kein Faktor über Fahrzeuge",
                gegner={"Rundtour": "Zufallsauswahl über alle acht Zugarten (E = 0)", "Einplanung": "ATC(k), k aus g Werten auf 20 Trainingsinstanzen gewählt (E = g)",
                        "Bin Packing": "Best Fit (E = 0); parametrische Regeln PR (21) und PR2 (64 bis 1 024)"})


def schreiben():
    (ROOT / "data").mkdir(exist_ok=True)
    karte = bauen_karte()
    (ROOT / "data" / "mek_karte.json").write_text(json.dumps(karte, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    (ROOT / "data" / "mek_kosten.json").write_text(json.dumps(bauen_kosten(), ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("Karte:", len(karte["zeilen"]), "Zeilen")


def check():
    gespeichert = json.loads((ROOT / "data" / "mek_karte.json").read_text(encoding="utf-8"))["zeilen"]
    neu = bauen_karte()["zeilen"]
    ids = {z["id"] for z in neu}
    fehler = [z["id"] for z in gespeichert if z["id"] in ids and z != next(n for n in neu if n["id"] == z["id"])]
    print("Abweichungen:", fehler or "keine", f"({len(gespeichert)} gespeichert, {len(neu)} neu gezählt)")
    return 1 if fehler else 0


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(check())
    schreiben()
