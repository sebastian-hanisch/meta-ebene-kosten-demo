"""Verdikte (reine Funktionen → (Art, Text)), Kostenbuch-Zeilen und die zwei Live-Rechnungen (Probe des Trainings, Zeitmessung).

Jede Zahl im Text kommt aus den Argumenten, nie aus dem Text selbst. Schwellen stehen in mek_constants (gesetzt, nicht abgeleitet)."""

import time
from statistics import median

import mek_constants as C
import mek_frozen as F
import mek_kosten as KO
import mek_select as SE
import mek_train as T
from mek_stats import PACKEN_TOL, mittel, packen_urteil, standardfehler


# ------------------------------------------------------------------ Format
def tsd(x: float) -> str:
    """Ganze Zahl mit Tausendertrennung durch Leerzeichen („1 455“)."""
    return f"{int(x + 0.5) if x >= 0 else -int(-x + 0.5):,}".replace(",", " ")


def dez(x: float, stellen: int = 1) -> str:
    """Dezimalzahl mit Komma; ab 1 000 mit Tausendertrennung."""
    if abs(x) >= 1000:
        return tsd(x)
    return f"{x:.{stellen}f}".replace(".", ",")


def pp(x: float, stellen: int = 2) -> str:
    """Prozentpunkte mit Vorzeichen und Komma."""
    return f"{x:+.{stellen}f}".replace(".", ",").replace("-", "−")


def faktor_text(f: float) -> str:
    """„15,6“ unter 100, sonst ganze Zahl mit Tausendertrennung („1 455“)."""
    return dez(f, 1) if f < 100 else tsd(f)


# ------------------------------------------------------------------ Verdikte
def verdict_kosten(verfahren: str, gegner: str, faktor: float, e_meta: float, e_gegner: float, einheit: str, besser: int, gleich: int, schlechter: int, m: int):
    """Frage 1: was kostet die Meta-Ebene vorab, und was bringt sie auf frischen Instanzen?
    success: besser in mindestens der Hälfte der Zellen; warning: besser in höchstens einem Achtel der Zellen und Faktor mindestens 10; sonst info."""
    if m <= 0 or besser + gleich + schlechter != m:
        raise ValueError("Die Zählung muss die Zellen aufteilen")
    text = (f"{verfahren} kostet das {faktor_text(faktor)}-Fache an Auswertungen von {gegner} ({tsd(e_meta)} gegen {tsd(e_gegner)}; Einheit: {einheit}) "
            f"und ist auf frischen Instanzen in {besser} von {m} Zellen besser, in {gleich} gleich, in {schlechter} schlechter.")
    if besser >= C.V_ERFOLG * m:
        return "success", text
    if besser <= C.V_WARN_ANTEIL * m and faktor >= C.V_WARN_FAKTOR:
        return "warning", text
    return "info", text


def verdict_aufschlag(verfahren: str, n_inst: int, e: float, b: float, einheit: str):
    """Frage 1 für eine Meta-Ebene ohne Gegner-Entwicklungskosten (Rundtour): Gesamtkosten gegen den Einsatz allein; immer info."""
    c = KO.gesamt(e, n_inst, b)
    if b <= 0 or n_inst <= 0:
        raise ValueError("N und b müssen positiv sein")
    return "info", (f"Bei N = {n_inst} Instanzen kostet {verfahren} insgesamt {tsd(c)} Auswertungen ({tsd(e)} Training plus {n_inst} mal {tsd(b)} Einsatz; Einheit: {einheit}), "
                    f"das {dez(KO.aufschlag(e, n_inst, b), 2)}-Fache des Einsatzes allein.")


def verdict_breakeven(z: dict, n_inst: int, art: str, k: int, akz: str, einsatz: str, lebensdauer=None):
    """Frage 2 (Rundtour): lohnt sich das Training bei N Instanzen? z kommt aus mek_frozen.zaehlung_lohnt.

    success: mindestens 2/3 der Zellen lohnen (in allen Wiederholungen) und der mittlere Gewinn liegt bei mindestens 0,25 Prozentpunkten; warning: höchstens 1/6 der Zellen lohnen
    (bei einer einzelnen Zelle: lohnt nicht oder Gewinn unter der Marke); sonst info."""
    m = z["zellen"]
    n_eff = n_inst if lebensdauer in (None, "nie") else min(n_inst, int(lebensdauer))
    text = (f"Bei N = {n_inst} Instanzen lohnt sich das Training ({C.ARTEN_ANZEIGE[art]}, K = {k}, {C.AKZ_ANZEIGE[akz]}, Einsatz {einsatz} Auswertungen je Instanz) "
            f"in {z['lohnt']} von {m} Zellen in allen Wiederholungen, in {z['nie_zellen']} Zellen in keiner Wiederholung (kein Gewinn bei gleichem Einsatzbudget); "
            f"mittlerer Gewinn {pp(z['gewinn'])} Prozentpunkte gegen die Zufallsauswahl. Voraussetzung: Instanzen aus derselben Verteilung wie im Training.")
    if n_eff < n_inst:
        text += f" Das Training hält nur {n_eff} Instanzen, gerechnet wird mit N = {n_eff}."
    if m == 1:
        return ("success" if z["lohnt"] == 1 and z["gewinn"] >= C.MARKE_GEWINN else "warning"), text
    if z["lohnt"] >= C.LOHNT_ANTEIL * m - 1e-9 and z["gewinn"] >= C.MARKE_GEWINN:
        return "success", text
    if z["lohnt"] <= C.LOHNT_WARN * m + 1e-9:
        return "warning", text
    return "info", text


def verdict_erzeugen(verfahren: str, gegner: str, faktor: float, besser: int, gleich: int, schlechter: int, m: int, anteil_train: float, anteil_test: float):
    """Frage 3: bringt mehr Aufwand beim Erzeugen mehr auf frischen Instanzen?
    warning: der Anteil der Läufe, die den Gegner schlagen, liegt auf frischen Instanzen um mehr als 20 Prozentpunkte unter dem auf dem Training und besser höchstens in einem Achtel der Zellen;
    success nur mit besser in mindestens der Hälfte der Zellen; sonst info."""
    if besser + gleich + schlechter != m:
        raise ValueError("Die Zählung muss die Zellen aufteilen")
    text = (f"{verfahren} kostet das {faktor_text(faktor)}-Fache von {gegner}; auf dem Training schlägt sie ihn in {dez(anteil_train, 0)} % der Läufe, auf frischen Instanzen in "
            f"{dez(anteil_test, 0)} %; {besser} / {gleich} / {schlechter} Zellen (besser / gleich / schlechter).")
    if besser >= C.V_ERFOLG * m:
        return "success", text
    if anteil_test < anteil_train - C.ERZEUGEN_LUECKE and besser <= C.V_WARN_ANTEIL * m:
        return "warning", text
    return "info", text


def verdict_karte(z: dict):
    """Frage 4: Verdikt einer Zeile der Karte. Zeilen „lohnt in k von m“: success ab 2/3, warning bis 1/6; Zeilen „besser / gleich / schlechter“: success ab der Hälfte
    der Zellen besser, warning bei höchstens einem Achtel; nicht gemessene Zeilen: info mit dem Satz „nicht gemessen“. Der Satz nennt Zählung, Einheit, Regel und Voraussetzung."""
    kopf = f"{z['meta_ebene']} gegen {z['gegner']} ({z['fahrzeug']}; {z['bedingung']})"
    if z["art"] == "nicht_gemessen":
        return "info", f"{kopf}: nicht gemessen. {z['voraussetzung']}."
    fuss = f" Einheit: {z['einheit']}. Entscheidungsregel: {z['regel']}. Voraussetzung: {z['voraussetzung']}."
    if z["art"] == "lohnt":
        k, m = z["k"], z["m"]
        text = f"{kopf}: lohnt in {k} von {m} Zellen (im Mittel der Wiederholungen in {z['k_mittel']})." + fuss
        if k >= C.KARTE_ERFOLG * m - 1e-9:
            return "success", text
        if k <= C.KARTE_WARN * m + 1e-9:
            return "warning", text
        return "info", text
    b, g, s, m = z["b"], z["g"], z["s"], z["m"]
    text = f"{kopf}: besser in {b} von {m} Zellen, gleich in {g}, schlechter in {s}." + fuss
    if b >= C.V_ERFOLG * m:
        return "success", text
    if b <= C.V_WARN_ANTEIL * m:
        return "warning", text
    return "info", text


def verdict_zeit(sekunden_je_1000: dict):
    """Frage 5: bei gleicher Auswertungszahl die Zeit je 1 000 Auswertungen verschieden? warning ab einem Verhältnis größter zu kleinster Wert von 1,25 (gesetzte Marke)."""
    werte = [v for v in sekunden_je_1000.values() if v is not None]
    if len(werte) < 2 or min(werte) <= 0:
        return "info", "Die Uhr hat zu grob gemessen (Zeit gleich null): kein Verhältnis berechenbar. Die Zähleinheit bleibt eine Wahl (Branke u. a. 2016)."
    f = max(werte) / min(werte)
    text = (f"Bei gleicher Auswertungszahl liegt die Zeit um das {dez(f, 2)}-Fache auseinander (auf diesem Rechner, in diesem Lauf); das sagt nichts über die Verfahren, "
            "nur dass „gleiche Auswertungszahl“ eine Wahl der Zähleinheit ist (Branke u. a. 2016).")
    return ("warning" if f >= C.ZEIT_VERHAELTNIS else "info"), text


def verdict_probe(mittel_diff: float, se: float, m: int, art: str):
    """Live-Probe von Frage 2: Mittel von „Zufallsauswahl minus trainiert“ (positiv = trainiert besser) ± Standardfehler über m Instanzen; keine N*-Zahl aus der Probe."""
    kopf = f"Probe mit {m} Testinstanzen: Zufallsauswahl minus {C.ARTEN_ANZEIGE[art]} {pp(mittel_diff)} ± {dez(se, 2)} Prozentpunkte (Standardfehler)."
    if abs(mittel_diff) < 2 * se:
        return "info", kopf + f" Bei {m} Instanzen nicht von null zu unterscheiden."
    if mittel_diff > 0:
        return "success", kopf + " Die trainierte Meta-Ebene ist bei gleichem Einsatz besser (mindestens zwei Standardfehler)."
    return "warning", kopf + " Die trainierte Meta-Ebene ist bei gleichem Einsatz schlechter (mindestens zwei Standardfehler)."


# ------------------------------------------------------------------ Kostenbuch
def _bgs_text(b, g, s, m):
    return f"{b} / {g} / {s} von {m} Zellen"


def rows_rundtour(n: int, k: int, art_unused, akz: str, stufe: str, n_inst: int) -> list[dict]:
    """Kostenbuch der Rundtour: Zeilen mit E, b, Gesamtkosten, Aufschlag und der gemessenen Wirkung. n: Orte der Zelle (nur für ℓ), akz und stufe wie in Frage 2."""
    lo = KO.kontrollstufe(n)
    b = lo if stufe == "lo" else 4 * lo
    zeilen = []
    karte = {r["id"]: r for r in (F.karte_zeilen("Rundtour") or [])}
    j = "klein" if stufe == "lo" else "gross"

    def kopf(name, e, wirkung, hinweis=""):
        return dict(Verfahren=name, Einheit="Auswertungen", E=e, b=b, gesamt=KO.gesamt(e, n_inst, b), aufschlag=(KO.aufschlag(e, n_inst, b) if e else 1.0), Wirkung=wirkung, Hinweis=hinweis)

    zeilen.append(kopf("Zufallsauswahl (Gegner)", 0, "Referenz"))
    for regel, name in (("cf", "online gelernt: Choice Function"), ("laut", "online gelernt: Lernautomat"), ("q", "online gelernt: Q-Lernen")):
        z = karte.get(f"rt-online-{regel}-{akz}-{j}")
        zeilen.append(kopf(name, 0, (_bgs_text(z["b"], z["g"], z["s"], z["m"]) + f", Mittel {pp(z['mittel'])} Pp") if z else "nicht gemessen",
                           "Kosten des Lernens stehen im Einsatz (Stück 3)"))
    for art in C.ARTEN:
        e = KO.entwicklung_rundtour(art, k, n)
        zl = F.zaehlung_lohnt(akz, "alle sechs", art, k, stufe, n_inst)
        zeilen.append(kopf(f"{C.ARTEN_ANZEIGE[art]} (K = {k})", e, f"lohnt in {zl['lohnt']} von {zl['zellen']} Zellen (alle Wiederholungen), Gewinn {pp(zl['gewinn'])} Pp"))
    t3 = karte.get(f"rt-t3-{akz}-{0 if stufe == 'lo' else 1}")
    zeilen.append(kopf("feste Teilmenge T3 ohne Training", 0, (_bgs_text(t3["b"], t3["g"], t3["s"], t3["m"]) + f", Mittel {pp(t3['mittel'])} Pp") if t3 else "nicht gemessen",
                       "nachträglich gewählt: die Kosten der Erkenntnis stehen nicht in der Bilanz (Zahl führt Stück 2)"))
    return zeilen


def rows_einplanung(regime: str, b: int, g: int, n_inst: int) -> list[dict]:
    """Kostenbuch der Einplanung für eine Suche mit b Auswertungen gegen ATC(k) mit g Werten: Zählung über die gemessenen Zellen, Anteile der Läufe, Knotenauswertungen."""
    zeilen = []
    n_train = 10 if regime == "klein" else 40
    # Hinweis: der Einsatz je Instanz ist eine Regel, 1/20 Auswertung
    atc_knoten = KO.knoten_je_auswertung(14, KO.TRAININGSINSTANZEN, n_train)
    zeilen.append(dict(Verfahren=f"ATC(k), k aus {g} Werten", E=g, b=1 / 20, faktor=1.0, besser=None, gleich=None, schlechter=None, m=None, train=None, test=None, knoten=atc_knoten,
                       Hinweis="Referenz; ATC ist als Baum mit 14 Knoten darstellbar"))
    for variante, name in (("zufall", "Zufallssuche über Bäume"), ("ones", "(1+1)-Suche über Bäume"), ("gp", "Genetische Programmierung (GP)"), ("gp_impf", "GP mit ATC als Startbaum")):
        m = F.ep_zellen_gemessen(variante, b)
        if not m:
            zeilen.append(dict(Verfahren=name, E=b, b=1 / 20, faktor=b / g, besser=None, gleich=None, schlechter=None, m=0, train=None, test=None, knoten=None, Hinweis="nicht gemessen"))
            continue
        bb, gg, ss = F.ep_zaehlung(variante, b, g)
        kn = None
        if variante == "gp":
            kn = int(F.ep_knoten_median(f"{regime}|M", b)) * KO.TRAININGSINSTANZEN * n_train * (n_train + 1) // 2
        zeilen.append(dict(Verfahren=name, E=b, b=1 / 20, faktor=b / g, besser=bb, gleich=gg, schlechter=ss, m=m, train=F.ep_anteil(variante, b, g, "train"), test=F.ep_anteil(variante, b, g, "test"),
                           knoten=kn, Hinweis=("Knoten: Median der Endregel in Familie M (Knoten × 20 × n (n + 1) / 2 je Auswertung der Endregel; Knotenzahl während der Suche nicht gemessen)" if kn else "")))
    return zeilen


def rows_packen(fam: str, k: int, gitter: int) -> list[dict]:
    """Kostenbuch Bin Packing für eine Familie: Best Fit, PR, PR2 mit g × g, Suche (200 und 1 000 Auswertungen) und Mengen (aus der Karte)."""
    g = F.gegner()["bin_packing"][fam]
    zeilen = [dict(Verfahren="Best Fit (Gegner)", E=0, b=1, Test="Referenz", Training="—")]
    zeilen.append(dict(Verfahren="PR (ein Parameter)", E=21, b=1, Test=f"Median {pp(float(median(g['pr']['test'])))} Pp, {packen_urteil(g['pr']['test'])['urteil']}", Training=f"Median {pp(float(median(g['pr']['train'])))} Pp"))
    for gi in C.BP_PR2_GRID:
        u = F.bp_pr2_urteil(fam, gi)
        zeilen.append(dict(Verfahren=f"PR2 mit {gi} × {gi} Gitter", E=gi * gi, b=1, Test=f"Median {pp(u['median'])} Pp, {u['urteil']}", Training=f"Median {pp(F.bp_pr2_median(fam, gi, 'train'))} Pp"))
    for methode in ("EA-S", "GP-T"):
        for budget in C.BP_BUDGETS:
            u = F.bp_suche_urteil(fam, methode, budget)
            zeilen.append(dict(Verfahren=f"{methode}, Suche mit {budget} Auswertungen", E=budget, b=1, Test=f"Median {pp(u['median'])} Pp, {u['urteil']}",
                               Training=f"Median {pp(F.bp_suche_median(fam, methode, budget, 'train'))} Pp"))
    karte = {r["id"]: r for r in (F.karte_zeilen("Bin Packing") or [])}
    for pool in ("EA-S", "GP-T"):
        z = karte.get(f"bp-menge-{pool}-orakel")
        zeilen.append(dict(Verfahren=f"Menge k = {k} aus dem Pool von {pool}, Orakelwahl", E=1000, b=k, Test=(_bgs_text(z["b"], z["g"], z["s"], z["m"]) + " (Familien)") if z else "nicht gemessen", Training="—"))
    return zeilen


# ------------------------------------------------------------------ Live-Probe des Trainings (Frage 2)
def probe_auswertungen_nach_budget(art: str, k: int, n: int = C.PROBE_N) -> int:
    """Auswertungen der Probe nach den Budgets gerechnet (ohne die tatsächlich verbrauchten zu zählen): Training (k Läufe, bei der Einzelheuristik 1 + 8 je Instanz)
    plus Einsatz auf den Testinstanzen (2 Läufe je Instanz, Zufallsauswahl und trainierte Variante) mit Budget ℓ = 50·n."""
    k = max(1, min(int(k), C.PROBE_K_MAX))
    lo = C.LO_F * n
    return k * lo * (1 if art == "mix" else 1 + C.K) + C.PROBE_INSTANZEN * C.PROBE_SEEDS * 2 * lo


def probe(akz: str, art: str, k: int, familie: str = "gleich", n: int = C.PROBE_N) -> dict:
    """Live-Probe: Training auf k ≤ 3 Trainingsinstanzen (Instanzen 5000 + j), Einsatz auf 8 Testinstanzen (0 bis 7) × 2 Läufe mit Budget ℓ = 50·n.

    Rückgabe: {"differenzen" (Zufallsauswahl minus trainiert je Instanz, Prozentpunkte gegen die Referenz aus mek_refs.json), "mittel", "se", "kosten" (Auswertungen), "p" bzw. "h"}.
    Aus der Probe entsteht keine N*-Zahl."""
    import json
    from pathlib import Path
    k = max(1, min(int(k), C.PROBE_K_MAX))
    refs = json.loads((Path(__file__).resolve().parent / "mek_refs.json").read_text(encoding="utf-8"))["refs"][familie][str(n)]
    lo = C.LO_F * n
    idxs = [5000 + j for j in range(k)]
    p, h = T.trainiere(familie, n, idxs, akz, einzel=(art == "einzel"))
    kosten = k * lo * (1 if art == "mix" else 1 + C.K)
    diffs = []
    for i in range(C.PROBE_INSTANZEN):
        ref = refs[i]
        g, m = [], []
        for s in range(C.PROBE_SEEDS):
            r, _ = T.lauf(familie, n, i, s, C.ALLE_ZUGARTEN, akz, lo, None, ())
            kosten += r["used"]
            g.append(r["best"])
            if art == "mix":
                r, _ = T.lauf(familie, n, i, s, C.ALLE_ZUGARTEN, akz, lo, T.MixSelector(p), ())
            else:
                r, _ = T.lauf(familie, n, i, s, (h,), akz, lo, None, ())
            kosten += r["used"]
            m.append(r["best"])
            ref = min(ref, g[-1], m[-1])
        diffs.append(100.0 * (mittel(g) - mittel(m)) / ref)
    return dict(differenzen=diffs, mittel=mittel(diffs), se=standardfehler(diffs), kosten=kosten, p=p, h=h, m=len(diffs))


# ------------------------------------------------------------------ Zeitmessung (Frage 5)
def zeit_messung(seed: int, regeln=C.ZEIT_REGELN, auswertungen: int = C.ZEIT_AUSWERTUNGEN, wdh: int = C.ZEIT_WDH, n: int = C.ZEIT_N, akz: str = "rr") -> list[dict]:
    """Je Regel: Anwendungen, Auswertungen, Sekunden (Median aus `wdh` Wiederholungen); Instanz = Zufalls-Seed `seed` der Zeitmessung. Zeiten sind nie ein Befund."""
    rows = []
    for regel in regeln:
        zeiten, apps, ev = [], [], []
        for w in range(wdh):
            _, D = T.instance("gleich", n, seed)
            t0 = T.S.start_tour(D, "gleich", n, seed, w)
            kante = T.S.tour_cost(D, t0) / n
            rng = T.BlockSplitMix64(T.S.run_seed("gleich", n, seed, w))
            if regel == "rand":
                arms, sel = C.ALLE_ZUGARTEN, None
            elif regel in ("cf", "laut", "q"):
                arms, sel = C.ALLE_ZUGARTEN, SE.make_selector(regel, C.K, kante)
            else:
                arms, sel = (int(regel[1:]),), None
            t_start = time.perf_counter()
            r = T.run_search(D, t0, auswertungen, arms, akz, rng, selector=sel)
            zeiten.append(time.perf_counter() - t_start)
            apps.append(r["steps"])
            ev.append(r["used"])
        sek = float(median(zeiten))
        rows.append(dict(regel=regel, Regel=C.ZEIT_ANZEIGE[regel], Anwendungen=int(median(apps)), Auswertungen=int(median(ev)), Sekunden=sek,
                         je1000=(1000.0 * sek / int(median(ev))) if median(ev) else None, je1000_anw=(1000.0 * sek / int(median(apps))) if median(apps) else None))
    return rows


# ------------------------------------------------------------------ Tabellen für Frage 2 und die Karte
def stern_text(s: dict) -> str:
    """N* als Text: Zahl, „nie“, „> Kurve“ oder „sofort“."""
    return {"ok": lambda: dez(s["wert"], 1), "nie": lambda: "nie", "ueber_kurve": lambda: "> Kurve", "sofort": lambda: "sofort"}[s["status"]]()


def stern_zelle_text(akz: str, zn: str, art: str, k: int, stufe: str) -> str:
    """N* einer Zelle aus dem Mittel der Wiederholungen, dahinter in Klammern die Spanne über die Wiederholungen („nie“ und „> Kurve“ einzeln gezählt)."""
    haupt = stern_text(F.stern(akz, zn, art, k, stufe))
    je = F.sterne_je_wdh(akz, zn, art, k, stufe)
    zahlen = [s["wert"] for s in je if s["status"] == "ok"]
    teile = []
    if zahlen:
        teile.append(f"{dez(min(zahlen), 1)} bis {dez(max(zahlen), 1)}")
    for status, wort in (("nie", "nie"), ("ueber_kurve", "> Kurve")):
        anz = sum(s["status"] == status for s in je)
        if anz:
            teile.append(f"{wort} {anz}×")
    return haupt + (f" ({'; '.join(teile)})" if teile else "")


def stern_tabelle(akz: str, zellen: list[str], art: str, stufe: str) -> list[dict]:
    """Zeilen für die Tabelle N* je Zelle × K, dazu der Gewinn bei gleichem Einsatz je K (Mittel der Wiederholungen, Prozentpunkte)."""
    out = []
    for zn in zellen:
        z = {"Zelle": zn}
        for k in C.H5_KS:
            z[f"K = {k}"] = stern_zelle_text(akz, zn, art, k, stufe)
        z["Gewinn K = 1 (Pp)"] = F.gewinn(akz, zn, art, 1, stufe)
        z["Gewinn K = 30 (Pp)"] = F.gewinn(akz, zn, art, 30, stufe)
        out.append(z)
    return out


def zaehlung_text(z: dict) -> str:
    """Zählung einer Zeile der Karte als Text."""
    if z["art"] == "nicht_gemessen":
        return "nicht gemessen"
    if z["art"] == "lohnt":
        return f"lohnt in {z['k']} von {z['m']} (Mittel: {z['k_mittel']})"
    return f"{z['b']} / {z['g']} / {z['s']} von {z['m']}"


# ------------------------------------------------------------------ Raster des Gegners (Frage 3)
def raster_aenderung_ep() -> dict:
    """Änderung des Medians des Regrets von ATC(k) bei 161 statt 11 k-Werten je Zelle in Prozentpunkten (negativ = der Gegner wird besser), über die acht Zellen."""
    d = {z: 100 * (F.ep_median_reue(z, "atc", g=161) - F.ep_median_reue(z, "atc", g=11)) for z in F.ep_zellen()}
    return dict(je_zelle=d, minimum=min(d.values()), maximum=max(d.values()), besser=sum(v < 0 for v in d.values()), schlechter=sum(v > 0 for v in d.values()))


def raster_aenderung_pr2() -> dict:
    """Änderung des Medians von Δ gegen Best Fit auf frischen Instanzen bei PR2 mit 1 024 statt 64 Auswertungen je Familie (Prozentpunkte, positiv = schlechter)."""
    d = {f: F.bp_pr2_median(f, 32, "test") - F.bp_pr2_median(f, 8, "test") for f in C.BP_FAMILIEN}
    return dict(je_familie=d, minimum=min(d.values()), maximum=max(d.values()))


def pr2_schwellenfall(fam: str = "stark", gitter: int = 32) -> dict:
    """PR2 in der breit gestreuten Familie mit dem größten Gitter: Median von Δ, Läufe schlechter als Best Fit, Urteil. Der Median liegt knapp unter der Schwelle (Schwellenartefakt „gleich“)."""
    u = F.bp_pr2_urteil(fam, gitter)
    return dict(median=u["median"], schlechter=u["laeufe_pos"], laeufe=u["n"], urteil=u["urteil"], schwelle=PACKEN_TOL)


def text_pr2_schwelle() -> str:
    """Satz zum Schwellenfall von PR2 (Zahlen aus der Datei)."""
    s = pr2_schwellenfall()
    return (f"In der breit gestreuten Familie liegt PR2 mit größerem Gitter zunehmend über Best Fit (Median {pp(s['median'], 4)} bei 1 024 Auswertungen, in {s['schlechter']} von {s['laeufe']} Läufen "
            f"schlechter); die Regel zählt „{s['urteil']}“, weil der Median knapp unter der Schwelle {dez(s['schwelle'], 1)} liegt.")


def text_raster(budget: int = 16000) -> str:
    """Satz unter Frage 3: was mehr Auswertungen des Gegners bewirken (Zahlen aus den Dateien)."""
    a = raster_aenderung_ep()
    p = raster_aenderung_pr2()
    z11 = F.ep_zaehlung("gp", budget, 11)
    z161 = F.ep_zaehlung("gp", budget, 161)
    return (f"Mit 161 statt 11 k-Werten ändert sich der Median des Regrets von ATC(k) in den acht Zellen um {pp(a['minimum'])} bis {pp(a['maximum'])} Prozentpunkte "
            f"(negativ = der Gegner wird besser; besser in {a['besser']}, schlechter in {a['schlechter']} Zellen). GP mit {tsd(budget)} Auswertungen steht gegen ATC mit 11 Werten bei {z11[0]} / {z11[1]} / {z11[2]} "
            f"(besser / gleich / schlechter), gegen ATC mit 161 Werten bei {z161[0]} / {z161[1]} / {z161[2]}. PR2 mit 1 024 statt 64 Auswertungen ändert den Median von Δ auf frischen Instanzen um "
            f"{pp(p['minimum'], 3)} bis {pp(p['maximum'], 3)} Prozentpunkte (positiv = schlechter), auf dem Training wird PR2 besser. " + text_pr2_schwelle())
