"""Rechnet die Budgetkurven der festen Gegner in Einplanung und Bin Packing vor und schreibt data/mek_gegner.json.

    python tools/mek_make_gegner.py messen       rechnet ATC(k) mit feinerem k-Raster (11, 41, 81, 161 Werte) und PR2 mit 8 × 8, 16 × 16, 32 × 32 Gitter
    python tools/mek_make_gegner.py --check      prüft die Proben (11er-Raster und 8 × 8-Gitter reproduzieren die gespeicherten Läufe der Nachbardemos)

Die Suchläufe (GP, (1+1), Zufallssuche; EA-S, GP-T und die anderen) werden **nicht** neu gerechnet: ihre Läufe stammen aus den eingefrorenen Dateien der
Stücke 5 (`prioritaetsregel-evolution-demo/data/prg_laeufe_*.json`) und 6 (`platzierungsfunktion-demo/plf_precomputed.json`), gerechnet mit demselben
Zufall (SplitMix64). Neu ist nur der Gegner mit seiner Budgetkurve: ATC(k) wählt k aus einem Raster von g Werten (geometrisch von 0,1 bis 6,0; g = 11 ist das
Raster von Stück 5) auf den 20 Trainingsinstanzen des Laufs und wird auf der Testzelle bewertet; PR2 wählt (λ, m) auf einem g × g-Gitter (λ in [0, 1], m in
[0,02, 0,4]) und wird auf den 200 Testinstanzen bewertet. Beides verwendet den Code der Nachbardemos (nur gelesen) und braucht die Nachbarordner."""

import json
import platform
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
PROJEKTE = ROOT.parent
sys.path.insert(0, str(ROOT))
for nachbar in ("prioritaetsregel-evolution-demo", "platzierungsfunktion-demo"):
    sys.path.insert(0, str(PROJEKTE / nachbar))

import mek_constants as C  # noqa: E402
from mek_stats import d1_urteil, packen_urteil  # noqa: E402

AUSGABE = ROOT / "data" / "mek_gegner.json"


# ------------------------------------------------------------------ Einplanung
def raster_atc(g: int):
    """k-Raster mit g Werten: g = 11 das Raster von Stück 5, sonst geometrisch von 0,1 bis 6,0."""
    import prg_algorithm as PA
    return list(PA.K_GRID) if g == 11 else [float(x) for x in np.geomspace(C.EP_K_VON, C.EP_K_BIS, g)]


def ep_zelle(regime: str, fam: str, rasters=C.EP_RASTER):
    """ATC(g) je Lauf der Zelle (Trainingsfamilie fam, n = Trainings-n): gewähltes k, Trainingssumme, Reue auf der eigenen Testzelle (Anteil)."""
    import prg_algorithm as PA
    import prg_evaluation as PE
    import prg_exact as PX  # noqa: F401
    import prg_measure as PM
    import prg_scenario as PS
    n = PS.REGIMES[regime]["n_train"]
    p, w, d, ref = PM.test_cell(regime, fam, n)
    daten = json.loads((PROJEKTE / "prioritaetsregel-evolution-demo" / "data" / f"prg_laeufe_{regime}.json").read_text(encoding="utf-8"))
    laeufe = sorted((r for r in daten["runs"] if r["fam"] == fam), key=lambda r: r["lauf"])
    zelle = f"{fam}|{n}"
    out = {g: {"k": [], "train": [], "reue": []} for g in rasters}
    for r in laeufe:
        tp, tw, td = PS.training_set(fam, n, r["lauf"])
        summen = {}

        def summe(k, tp=tp, tw=tw, td=td, summen=summen):
            if k not in summen:
                summen[k] = float(PA.train_sum(tp, tw, td, PA.rule_atc(k)))
            return summen[k]
        cache = {}
        for g in rasters:
            kb = min(raster_atc(g), key=lambda k: (summe(k), k))
            if kb not in cache:
                cache[kb] = PE.regret(PA.dispatch(p, w, d, PA.rule_atc(kb))[0], ref)
            out[g]["k"].append(kb)
            out[g]["train"].append(summe(kb))
            out[g]["reue"].append(cache[kb])
        # Probe: das Raster mit 11 Werten reproduziert Stück 5
        assert abs(out[11]["reue"][-1] - r["atc_test"][zelle]) < 1e-7, (regime, fam, r["lauf"], out[11]["reue"][-1], r["atc_test"][zelle])
        assert out[11]["k"][-1] == r["k"]
    return laeufe, out


def daten_fest(regime: str) -> dict:
    """Reue der vier festen Regeln je Testzelle aus Stück 5."""
    d = json.loads((PROJEKTE / "prioritaetsregel-evolution-demo" / "data" / f"prg_laeufe_{regime}.json").read_text(encoding="utf-8"))
    return d["fixed_test"]


def einplanung():
    res = {}
    for regime in C.EP_REGIME:
        for fam in C.EP_FAMILIEN:
            t0 = time.time()
            laeufe, atc = ep_zelle(regime, fam)
            n = {"klein": 10, "gross": 40}[regime]
            zelle = f"{fam}|{n}"
            eintrag = {"n_train": n, "laeufe": len(laeufe), "atc": {str(g): {k: [round(x, 10) for x in v] for k, v in a.items()} for g, a in atc.items()}}
            for variante in ("gp", "ones", "zufall", "gp_impf"):
                je_b = {}
                for b in C.EP_BUDGETS:
                    zeilen = [next((e for e in r["res"] if e["v"] == variante and e["B"] == b), None) for r in laeufe]
                    if any(z is None for z in zeilen):
                        break
                    je_b[str(b)] = {"reue": [z["test"][zelle] for z in zeilen], "train": [z["train"] for z in zeilen]}
                if je_b:
                    eintrag[variante] = je_b
            eintrag["fest"] = {k: round(v, 10) for k, v in daten_fest(regime)[zelle].items()}
            eintrag["groesse_gp"] = {str(b): [next(e for e in r["res"] if e["v"] == "gp" and e["B"] == b)["size"] for r in laeufe] for b in C.EP_B}
            res[f"{regime}|{fam}"] = eintrag
            print(f"Einplanung {regime}|{fam} {time.time() - t0:.0f} s", flush=True)
    return res


# ------------------------------------------------------------------ Bin Packing
def bp_zelle(familie: str, gitter=C.BP_PR2_GRID):
    import plf_algorithm as A
    import plf_evaluation as E
    import plf_scenario as S
    test = S.test_set(familie)
    lbt = A.lower_bound(test)
    bft = A.run_known(test, "BF")
    out = {g: {"lam": [], "m": [], "train": [], "test": []} for g in gitter}
    pre = json.loads((PROJEKTE / "platzierungsfunktion-demo" / "plf_precomputed.json").read_text(encoding="utf-8"))
    for lauf in range(C.BP_LAEUFE):
        train = S.training_set(familie, lauf)
        lb = A.lower_bound(train)
        bf_fit = A.fitness(A.run_known(train, "BF"), lb)
        for g in gitter:
            lams = [float(x) for x in np.linspace(*C.BP_PR2_LAMBDA, g)]
            ms = [float(x) for x in np.linspace(*C.BP_PR2_M, g)]
            fits = {}
            best = None
            for lam in lams:
                for m in ms:
                    fits[(lam, m)] = A.fitness(A.simulate(train, A.score_pr2(lam, m))[0], lb)
                    if best is None or fits[(lam, m)] < fits[best] - 1e-12:
                        best = (lam, m)
            bins = A.simulate(test, A.score_pr2(*best))[0]
            out[g]["lam"].append(best[0])
            out[g]["m"].append(best[1])
            out[g]["train"].append(100.0 * (fits[best] - bf_fit))
            out[g]["test"].append(E.delta_pp(bins, bft, lbt))
        if 8 in gitter:
            rec = pre["m2"][familie][lauf]["PR2"]
            assert abs(rec["lam"] - out[8]["lam"][-1]) < 1e-12 and abs(rec["m"] - out[8]["m"][-1]) < 1e-12, (familie, lauf)
            assert abs(rec["test"] - out[8]["test"][-1]) < 1e-9, (familie, lauf)
    return out, pre


def bin_packing():
    res = {}
    for fam in C.BP_FAMILIEN:
        t0 = time.time()
        pr2, pre = bp_zelle(fam)
        eintrag = {"pr2": {str(g): {k: [round(x, 10) for x in v] for k, v in a.items()} for g, a in pr2.items()}}
        suche = {}
        for methode, laeufe in pre["m1"][fam].items():
            suche[methode] = {str(c["n"]): {"train": [], "test": []} for c in laeufe[0]["cps"]}
            for r in laeufe:
                for c in r["cps"]:
                    suche[methode][str(c["n"])]["train"].append(round(c["train"], 10))
                    suche[methode][str(c["n"])]["test"].append(round(c["test"], 10))
        eintrag["suche"] = suche
        eintrag["pr"] = {"train": [round(r["PR"]["train"], 10) for r in pre["m2"][fam]], "test": [round(r["PR"]["test"], 10) for r in pre["m2"][fam]]}
        eintrag["bfix"] = {"train": [round(r["BFIX"]["train"], 10) for r in pre["m2"][fam]], "test": [round(r["BFIX"]["test"], 10) for r in pre["m2"][fam]]}
        res[fam] = eintrag
        print(f"Bin Packing {fam} {time.time() - t0:.0f} s", flush=True)
    return res


def messen() -> None:
    t0 = time.time()
    ep = einplanung()
    bp = bin_packing()
    meta = dict(schema=1, rasters_atc=list(C.EP_RASTER), k_bereich=[C.EP_K_VON, C.EP_K_BIS], pr2_gitter=list(C.BP_PR2_GRID), laeufe=20, python=platform.python_version(),
                rechner=platform.system(), sekunden=round(time.time() - t0), zufall="SplitMix64 (Nachbardemos prg_rng.py und plf_rng.py)",
                quellen="prg_laeufe_klein.json, prg_laeufe_gross.json (Stück 5); plf_precomputed.json (Stück 6); ATC(g) und PR2-Gitter neu gerechnet",
                einheit_ep="Reue als Anteil (0,01 = ein Prozentpunkt); Auswertung = Regel auf 20 Trainingsinstanzen",
                einheit_bp="Prozentpunkte Überschuss gegen Best Fit, positiv = schlechter; Auswertung = Regel auf 20 Trainingsinstanzen")
    AUSGABE.parent.mkdir(exist_ok=True)
    AUSGABE.write_text(json.dumps(dict(meta=meta, einplanung=ep, bin_packing=bp), separators=(",", ":"), ensure_ascii=False), encoding="utf-8", newline="\n")
    print("geschrieben:", AUSGABE, f"{AUSGABE.stat().st_size / 1e6:.2f} MB", flush=True)
    for regime in C.EP_REGIME:
        zaehl = {g: {b: [0, 0, 0] for b in C.EP_B} for g in C.EP_RASTER}
        for fam in C.EP_FAMILIEN:
            e = ep[f"{regime}|{fam}"]
            for g in C.EP_RASTER:
                for b in C.EP_B:
                    u = d1_urteil([a - c for a, c in zip(e["gp"][str(b)]["reue"], e["atc"][str(g)]["reue"])])["urteil"]
                    zaehl[g][b][("besser", "gleich", "schlechter").index(u)] += 1
        print(regime, {g: {b: tuple(v) for b, v in z.items()} for g, z in zaehl.items()})
    for fam in C.BP_FAMILIEN:
        print(fam, {g: packen_urteil(bp[fam]["pr2"][str(g)]["test"])["urteil"] for g in C.BP_PR2_GRID})


if __name__ == "__main__":
    if "--check" in sys.argv:
        ep_zelle("klein", "E")
        bp_zelle("gl_20_70", gitter=(8,))
        print("Proben bestanden")
    else:
        messen()
