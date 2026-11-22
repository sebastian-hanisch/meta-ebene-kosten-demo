"""Eingefrorene Messreihen (`data/mek_*.json`): laden, Schema prüfen, zu Break-even, Zählungen und Tabellen zusammenfassen.

Alle Zählungen (D1-Urteile, Break-even N*, Anteile, Mediane) werden hier aus den gespeicherten Einzelwerten gerechnet, nicht fertig gelesen.
Fehlt eine Datei oder eine Zeile, antwortet der Lader mit None statt mit einem Absturz (die Seite zeigt dann „nicht gemessen“)."""

import json
from functools import lru_cache
from pathlib import Path
from statistics import median

import mek_breakeven as BE
import mek_constants as C
import mek_kosten as KO
from mek_stats import d1_urteil, mittel, packen_urteil, zaehle

DATA = Path(__file__).resolve().parent / "data"


@lru_cache(maxsize=None)
def laden(name: str):
    """Liest `data/mek_<name>.json`; None, wenn die Datei fehlt."""
    pfad = DATA / f"mek_{name}.json"
    if not pfad.exists():
        return None
    return json.loads(pfad.read_text(encoding="utf-8"))


def h5():
    return laden("h5")


def gegner():
    return laden("gegner")


def karte():
    return laden("karte")


def schema_fehler_h5(d) -> list[str]:
    """Fehlerliste (leer = in Ordnung) für mek_h5.json."""
    f = []
    meta = d["meta"]
    if meta["zellen"] != [f"{a}/{n}" for a, n in C.H5_ZELLEN] or meta["ks"] != list(C.H5_KS) or meta["mults"] != list(C.H5_MULTS):
        f.append("meta: Zellen, K oder Stützstellen")
    for akz in C.H5_AKZ:
        for zn in meta["zellen"]:
            if len(d["kurve"][akz][zn]) != len(C.H5_MULTS):
                f.append(f"kurve {akz} {zn}")
            m = d["mix"][akz][zn]
            if len(m) != meta["wiederholungen"] or any(len(z) != len(C.H5_KS) for z in m):
                f.append(f"mix {akz} {zn}")
            if len(d["kurve_inst"][akz][zn]) != meta["instanzen"]:
                f.append(f"kurve_inst {akz} {zn}")
    return f


# ------------------------------------------------------------------ H5: Break-even
def zellen_namen(auswahl: str) -> list[str]:
    """Die Zellen einer Auswahl („alle sechs“ oder eine Zelle wie „gleich/30“)."""
    alle = [f"{f}/{n}" for f, n in C.H5_ZELLEN]
    return alle if auswahl == "alle sechs" else [auswahl]


def stufe_index(stufe: str) -> tuple[int, int]:
    """(Index in der Kurve, Index in der Mischung) für lo und hi: b_M = 1 bzw. 4 mal ℓ."""
    b = 1 if stufe == "lo" else 4
    return C.H5_MULTS.index(b), 0 if stufe == "lo" else 1


def rand_bei(akz: str, zn: str, stufe: str) -> float:
    return h5()["kurve"][akz][zn][stufe_index(stufe)[0]]


def trainiert_gap(akz: str, zn: str, art: str, k: int, stufe: str, wdh: int) -> float:
    """Mittlerer Abstand der trainierten Meta-Ebene (Mischung oder gelernte Einzelheuristik) einer Wiederholung bei Einsatz lo bzw. hi."""
    d = h5()
    ki = C.H5_KS.index(k)
    if art == "mix":
        return d["mix"][akz][zn][wdh][ki][stufe_index(stufe)[1]]
    h = d["einzel"][akz][zn][wdh][ki]
    return d["einzel_alle"][akz][zn][stufe][h]


def stern(akz: str, zn: str, art: str, k: int, stufe: str, wdh: int | None = None) -> dict:
    """Break-even N* einer Zelle: je Wiederholung (`wdh` = Nummer) oder aus dem Mittel der Wiederholungen (`wdh` None, wie die Vormessung)."""
    d = h5()
    kurve = d["kurve"][akz][zn]
    if wdh is None:
        q = mittel(trainiert_gap(akz, zn, art, k, stufe, w) for w in range(d["meta"]["wiederholungen"]))
    else:
        q = trainiert_gap(akz, zn, art, k, stufe, wdh)
    b_m = 1 if stufe == "lo" else 4
    return BE.n_stern(C.H5_MULTS, kurve, q, b_m, KO.entwicklung_in_stufen(art, k))


def sterne_je_wdh(akz, zn, art, k, stufe) -> list[dict]:
    return [stern(akz, zn, art, k, stufe, w) for w in range(h5()["meta"]["wiederholungen"])]


def gewinn(akz: str, zn: str, art: str, k: int, stufe: str) -> float:
    """Unterschied „Gegner minus trainiert“ bei gleichem Einsatzbudget in Prozentpunkten, Mittel der Wiederholungen (positiv = trainiert besser)."""
    d = h5()
    q = mittel(trainiert_gap(akz, zn, art, k, stufe, w) for w in range(d["meta"]["wiederholungen"]))
    return rand_bei(akz, zn, stufe) - q


def gewinn_spanne(akz, zn, art, k, stufe) -> tuple[float, float]:
    d = h5()
    r = rand_bei(akz, zn, stufe)
    werte = [r - trainiert_gap(akz, zn, art, k, stufe, w) for w in range(d["meta"]["wiederholungen"])]
    return min(werte), max(werte)


def zelle_lohnt(akz, zn, art, k, stufe, n_inst: float, lebensdauer=None) -> dict:
    """Lohnt sich das Training in dieser Zelle bei n_inst Instanzen? „Lohnt“ heißt: in allen Wiederholungen N* <= min(N, R) (R: Lebensdauer des Trainings).

    Rückgabe: {"lohnt", "mittel" (N* aus dem Mittel lohnt), "wdh_lohnen" (Zahl der lohnenden Wiederholungen), "wdh", "nie" (Zahl der Wiederholungen ohne Gewinn)}."""
    n_eff = n_inst if lebensdauer in (None, "nie") else min(n_inst, float(lebensdauer))
    je = sterne_je_wdh(akz, zn, art, k, stufe)
    lohnend = [BE.lohnt(s, n_eff) for s in je]
    return {"lohnt": all(lohnend), "mittel": BE.lohnt(stern(akz, zn, art, k, stufe), n_eff), "wdh_lohnen": sum(lohnend), "wdh": len(je),
            "nie": sum(s["status"] == "nie" for s in je)}


def zaehlung_lohnt(akz, auswahl, art, k, stufe, n_inst, lebensdauer=None) -> dict:
    """Zählung über die gewählten Zellen: in wie vielen lohnt das Training (alle Wiederholungen), im Mittel, nie; dazu mittlerer Gewinn in Prozentpunkten."""
    zn = zellen_namen(auswahl)
    z = [zelle_lohnt(akz, x, art, k, stufe, n_inst, lebensdauer) for x in zn]
    return {"zellen": len(zn), "lohnt": sum(x["lohnt"] for x in z), "mittel": sum(x["mittel"] for x in z), "nie_zellen": sum(x["wdh_lohnen"] == 0 and x["nie"] == x["wdh"] for x in z),
            "gewinn": mittel(gewinn(akz, x, art, k, stufe) for x in zn)}


# ------------------------------------------------------------------ Einplanung
def ep_zellen(regime: str | None = None) -> list[str]:
    regs = C.EP_REGIME if regime is None else (regime,)
    return [f"{r}|{f}" for r in regs for f in C.EP_FAMILIEN]


def ep_deltas(zelle: str, variante: str, b: int, g: int) -> list[float] | None:
    """Differenzen Reue(Variante) − Reue(ATC mit g Werten) je Lauf; None, wenn die Variante in der Zelle nicht gemessen ist."""
    e = gegner()["einplanung"][zelle]
    if variante not in e or str(b) not in e[variante]:
        return None
    return [a - c for a, c in zip(e[variante][str(b)]["reue"], e["atc"][str(g)]["reue"])]


def ep_urteile(variante: str, b: int, g: int, regime: str | None = None) -> list[str]:
    out = []
    for z in ep_zellen(regime):
        dl = ep_deltas(z, variante, b, g)
        if dl is not None:
            out.append(d1_urteil(dl)["urteil"])
    return out


def ep_zaehlung(variante: str, b: int, g: int, regime: str | None = None) -> tuple[int, int, int]:
    """(besser, gleich, schlechter) der Variante gegen ATC(g) nach Regel D1 über die gemessenen Zellen (höchstens acht)."""
    return zaehle(ep_urteile(variante, b, g, regime))


def ep_zellen_gemessen(variante: str, b: int, regime: str | None = None) -> int:
    return sum(1 for z in ep_zellen(regime) if variante in gegner()["einplanung"][z] and str(b) in gegner()["einplanung"][z][variante])


def ep_gegen_fest(b: int, regime: str | None = None) -> tuple[int, int, int]:
    """GP gegen die beste feste Regel (SPT, EDD, WSPT, MDD) der Testzelle nach Regel D1."""
    u = []
    for z in ep_zellen(regime):
        e = gegner()["einplanung"][z]
        best = min(e["fest"].values())
        u.append(d1_urteil([x - best for x in e["gp"][str(b)]["reue"]])["urteil"])
    return zaehle(u)


def ep_anteil(variante: str, b: int, g: int, art: str, regime: str | None = None) -> float | None:
    """Anteil der Läufe (in Prozent), in denen die Endregel besser ist als ATC(g): auf dem Training (Summe) oder auf der Testzelle (Reue)."""
    n = hits = 0
    for z in ep_zellen(regime):
        e = gegner()["einplanung"][z]
        if variante not in e or str(b) not in e[variante]:
            continue
        a = e[variante][str(b)]
        if art == "train":
            hits += sum(x < y for x, y in zip(a["train"], e["atc"][str(g)]["train"]))
        else:
            hits += sum(x < y for x, y in zip(a["reue"], e["atc"][str(g)]["reue"]))
        n += len(a["reue"])
    return None if n == 0 else 100.0 * hits / n


def ep_median_reue(zelle: str, variante: str, b: int | None = None, g: int | None = None) -> float | None:
    """Median der Reue über die 20 Läufe (Anteil) für GP-Varianten bei Budget b oder für ATC(g)."""
    e = gegner()["einplanung"][zelle]
    if variante == "atc":
        return float(median(e["atc"][str(g)]["reue"]))
    if variante not in e or str(b) not in e[variante]:
        return None
    return float(median(e[variante][str(b)]["reue"]))


def ep_kurve(zelle: str, variante: str) -> dict:
    """Median der Reue je Budget für eine Suchvariante: {B: Median}."""
    e = gegner()["einplanung"][zelle]
    return {int(b): float(median(v["reue"])) for b, v in e.get(variante, {}).items()}


def ep_knoten_median(zelle: str, b: int) -> float:
    e = gegner()["einplanung"][zelle]
    return float(median(e["groesse_gp"][str(b)]))


# ------------------------------------------------------------------ Bin Packing
def bp_suche_urteil(fam: str, methode: str, budget: int) -> dict:
    s = gegner()["bin_packing"][fam]["suche"][methode][str(budget)]
    return packen_urteil(s["test"])


def bp_suche_zaehlung(budget: int, methoden=None) -> tuple[int, int, int]:
    """(besser, gleich, schlechter) der Suchverfahren gegen Best Fit nach der Regel der Platzierungsfunktionen über Verfahren × Familien."""
    g = gegner()["bin_packing"]
    u = []
    for fam in C.BP_FAMILIEN:
        for m in (methoden or list(g[fam]["suche"])):
            u.append(packen_urteil(g[fam]["suche"][m][str(budget)]["test"])["urteil"])
    return zaehle(u)


def bp_pr2_urteil(fam: str, gitter: int) -> dict:
    """PR2 mit g × g Gitter (g = 8, 16, 32) gegen Best Fit."""
    return packen_urteil(gegner()["bin_packing"][fam]["pr2"][str(gitter)]["test"])


def bp_pr2_median(fam: str, gitter: int, art: str = "test") -> float:
    return float(median(gegner()["bin_packing"][fam]["pr2"][str(gitter)][art]))


def bp_suche_median(fam: str, methode: str, budget: int, art: str = "test") -> float:
    return float(median(gegner()["bin_packing"][fam]["suche"][methode][str(budget)][art]))


def bp_pr2_auswertungen(gitter: int) -> int:
    return gitter * gitter


def bp_anteil_besser(fam: str, methode: str, budget: int, art: str) -> float:
    s = gegner()["bin_packing"][fam]["suche"][methode][str(budget)][art]
    return 100.0 * sum(x < 0 for x in s) / len(s)


# ------------------------------------------------------------------ Karte und Kosten
def karte_zeilen(fahrzeug: str = "alle", nur_stabil: bool = False) -> list[dict]:
    k = karte()
    if k is None:
        return []
    rows = k["zeilen"]
    if fahrzeug != "alle":
        rows = [r for r in rows if r["fahrzeug"] == fahrzeug]
    if nur_stabil:
        rows = [r for r in rows if r.get("stabil", True)]
    return rows
