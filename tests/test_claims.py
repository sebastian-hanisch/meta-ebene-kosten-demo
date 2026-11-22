"""Claims der README: jede Zahl mit Messbezug wird unabhängig aus den eingefrorenen Dateien nachgerechnet (anderer Rechenweg als die App: numpy-Interpolation, scipy)
und muss in der README stehen. Zeilen ohne Test heißen in der README „Messungen dieser README, nicht im Test“."""

import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path
from statistics import median

import numpy as np
import pytest

import mek_constants as C
import mek_frozen as F
import mek_texts as TX

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8").replace("\r\n", "\n")
H5 = json.loads((ROOT / "data" / "mek_h5.json").read_text(encoding="utf-8"))
GEG = json.loads((ROOT / "data" / "mek_gegner.json").read_text(encoding="utf-8"))
M = np.array(C.H5_MULTS, dtype=float)


def _vz(x, stellen=2):
    """Zahl mit Vorzeichen, Komma und Minuszeichen wie in der README."""
    return f"{x:+.{stellen}f}".replace(".", ",").replace("-", "−")


def _qf(kurve, beta):
    """Q_F(β) mit numpy: linear in ln β (anderer Rechenweg als mek_breakeven)."""
    return float(np.interp(math.log(beta), np.log(M), kurve))


def _stern_enum(kurve, q, b, e, n_max=5000):
    for n in range(1, n_max + 1):
        if q <= _qf(kurve, b + e / n) + 1e-12:
            return n
    return None


def _lohnt_zellen(akz, art, k, stufe, n=30):
    """(Zellen, in denen in allen Wiederholungen N* <= n gilt; Zellen, in denen es nach dem Mittel der Wiederholungen gilt) aus den Rohwerten der Datei."""
    b = 1 if stufe == "lo" else 4
    e = k * (1 if art == "mix" else 8)
    alle = mittel = 0
    for zn in H5["meta"]["zellen"]:
        kurve = H5["kurve"][akz][zn]
        ki = C.H5_KS.index(k)
        qs = []
        for w in range(H5["meta"]["wiederholungen"]):
            if art == "mix":
                qs.append(H5["mix"][akz][zn][w][ki][0 if stufe == "lo" else 1])
            else:
                qs.append(H5["einzel_alle"][akz][zn][stufe][H5["einzel"][akz][zn][w][ki]])

        def ok(q):
            if q >= _qf(kurve, b):
                return False
            s = _stern_enum(kurve, q, b, e)
            return s is not None and s <= n
        alle += all(ok(q) for q in qs)
        mittel += ok(sum(qs) / len(qs))
    return alle, mittel


def _gewinn(akz, k, stufe):
    b = 1 if stufe == "lo" else 4
    ki = C.H5_KS.index(k)
    werte = []
    for zn in H5["meta"]["zellen"]:
        q = np.mean([H5["mix"][akz][zn][w][ki][0 if stufe == "lo" else 1] for w in range(5)])
        werte.append(_qf(H5["kurve"][akz][zn], b) - q)
    return float(np.mean(werte))


def _tab(akz, stufe, art, ks):
    z = {k: _lohnt_zellen(akz, art, k, stufe) for k in ks}
    return ", ".join(f"K = {k}: {z[k][0]} von 6 (Mittel {z[k][1]})" for k in ks)


@pytest.mark.parametrize("akz,stufe", [("rr", "lo"), ("la", "lo"), ("rr", "hi"), ("la", "hi")])
def test_lohnt_zaehlung(akz, stufe):
    """Die Zählung „lohnt in k von 6 Zellen“ aus den Rohwerten (Aufzählung ganzer Zahlen, numpy) steht in der README und ist gleich der der App."""
    assert _tab(akz, stufe, "mix", (1, 3, 10, 30)) in README
    for k in (1, 3, 10, 30):
        z = F.zaehlung_lohnt(akz, "alle sechs", "mix", k, stufe, 30)
        assert (z["lohnt"], z["mittel"]) == _lohnt_zellen(akz, "mix", k, stufe)
    z = F.zaehlung_lohnt(akz, "alle sechs", "einzel", 3, stufe, 30)
    assert (z["lohnt"], z["mittel"]) == _lohnt_zellen(akz, "einzel", 3, stufe)


def test_hook_late_acceptance_keine_zelle_und_regel_der_vormessung_nicht_erfuellt():
    for k in (1, 3, 10, 30):
        assert _lohnt_zellen("la", "mix", k, "lo")[0] == 0
    assert _lohnt_zellen("rr", "mix", 1, "lo")[0] >= 4
    assert _lohnt_zellen("rr", "mix", 10, "lo")[1] < 4          # Vorab-Regel der Vormessung „N* ≤ 30 in mindestens 4 von 6 Zellen mit K = 10“ nicht erfüllt


def test_gewinn():
    for akz, stufe in (("rr", "lo"), ("rr", "hi"), ("la", "lo")):
        for k in C.H5_KS:
            g = _gewinn(akz, k, stufe)
            assert sum(F.gewinn(akz, zn, "mix", k, stufe) for zn in F.zellen_namen("alle sechs")) / 6 == pytest.approx(g, abs=1e-9)
            if (akz, stufe) == ("rr", "lo"):
                assert _vz(g) in README, (akz, k, stufe, g)
    assert all(_gewinn("rr", k, "lo") > 0.25 for k in C.H5_KS) and all(_gewinn("la", k, "lo") < 0 for k in C.H5_KS)        # die Akzeptanz kehrt das Vorzeichen um
    hi = [_gewinn("rr", k, "hi") for k in C.H5_KS]
    assert _vz(min(hi)) in README and _vz(max(hi)) in README
    la = [_gewinn("la", k, "lo") for k in C.H5_KS]
    assert _vz(min(la)) in README and _vz(max(la)) in README


def test_faktoren():
    assert [round(b / 11, 1) for b in (1000, 4000, 16000)] == [90.9, 363.6, 1454.5]
    assert [round(b / 161, 1) for b in (1000, 4000, 16000)] == [6.2, 24.8, 99.4]
    for s in ("90,9", "364", "1 455", "6,2", "24,8", "99,4"):
        assert s in README


def _d1_scipy(deltas):
    stats = pytest.importorskip("scipy.stats")
    neg = sum(x < 0 for x in deltas) / len(deltas)
    pos = sum(x > 0 for x in deltas) / len(deltas)
    med = float(median(deltas))
    nz = [x for x in deltas if x != 0]
    p = float(stats.wilcoxon(nz, method="auto").pvalue) if nz else 1.0
    if neg >= 0.75 and med <= -0.01 and p < 0.01:
        return "besser"
    if pos >= 0.75 and med >= 0.01 and p < 0.01:
        return "schlechter"
    return "gleich"


def _zaehl_ep(b, g):
    u = []
    for regime in C.EP_REGIME:
        for fam in C.EP_FAMILIEN:
            e = GEG["einplanung"][f"{regime}|{fam}"]
            u.append(_d1_scipy([x - y for x, y in zip(e["gp"][str(b)]["reue"], e["atc"][str(g)]["reue"])]))
    return tuple(u.count(x) for x in ("besser", "gleich", "schlechter"))


@pytest.mark.parametrize("b,g", [(16000, 11), (16000, 161), (4000, 11), (1000, 11), (16000, 41), (16000, 81)])
def test_gp_gegen_atc(b, g):
    """Regel D1 mit scipy (Wilcoxon) nachgezählt; mit Bindungen rechnet scipy eine Näherung, die Zählung muss trotzdem gleich sein."""
    z = F.ep_zaehlung("gp", b, g)
    assert _zaehl_ep(b, g) == z
    assert f"{z[0]} / {z[1]} / {z[2]}" in README


def test_gp_gegen_atc_weitere_zahlen():
    for b in C.EP_B:
        assert sum(F.ep_gegen_fest(b)) == 8
    assert F.ep_gegen_fest(16000)[0] == 8                         # Anker: bei 16 000 Auswertungen 8 von 8 gegen die festen Regeln (nicht gegen ATC)
    for regime in C.EP_REGIME:
        tr = te = n = 0
        for fam in C.EP_FAMILIEN:
            e = GEG["einplanung"][f"{regime}|{fam}"]
            tr += sum(a < c for a, c in zip(e["gp"]["16000"]["train"], e["atc"]["11"]["train"]))
            te += sum(a < c for a, c in zip(e["gp"]["16000"]["reue"], e["atc"]["11"]["reue"]))
            n += 20
        assert F.ep_anteil("gp", 16000, 11, "train", regime) == pytest.approx(100 * tr / n)
        assert f"{100 * tr / n:.0f} %" in README and f"{100 * te / n:.0f} %" in README
    aend = [100 * (median(GEG["einplanung"][f"{r}|{f}"]["atc"]["161"]["reue"]) - median(GEG["einplanung"][f"{r}|{f}"]["atc"]["11"]["reue"])) for r in C.EP_REGIME for f in C.EP_FAMILIEN]
    assert _vz(min(aend)) in README and _vz(max(aend)) in README
    assert f"besser in {sum(a < 0 for a in aend)}, schlechter in {sum(a > 0 for a in aend)} von 8 Zellen" in README


def _packen_urteil(d):
    med = float(median(d))
    neg = sum(x < 0 for x in d)
    pos = sum(x > 0 for x in d)
    return "besser" if med <= -0.2 and neg >= 15 else ("schlechter" if med >= 0.2 and pos >= 15 else "gleich")


def test_bin_packing():
    bp = GEG["bin_packing"]
    for budget in ("200", "1000"):
        u = [_packen_urteil(bp[f]["suche"][m][budget]["test"]) for f in bp for m in bp[f]["suche"]]
        assert len(u) == 21 and u.count("besser") == 0
        assert F.bp_suche_zaehlung(int(budget)) == tuple(u.count(x) for x in ("besser", "gleich", "schlechter"))
    assert "0 von 21 Zellen besser" in README
    for g in ("8", "16", "32"):
        assert all(_packen_urteil(bp[f]["pr2"][g]["test"]) == "gleich" for f in bp)
        assert all(len(bp[f]["pr2"][g]["test"]) == 20 for f in bp)
        assert " / ".join(_vz(median(bp[f]["pr2"][g]["test"]), 3) for f in bp) in README
    assert "alle 9 Zellen nach der Regel „gleich“" in README
    for f in bp:
        assert median(bp[f]["pr2"]["8"]["train"]) < 0 and median(bp[f]["pr2"]["32"]["train"]) <= median(bp[f]["pr2"]["8"]["train"]) + 1e-9
        assert all(median(bp[f]["suche"][m]["1000"]["train"]) < 0 for m in ("EA-S", "GP-T"))
    assert " / ".join(_vz(median(bp[f]["suche"]["EA-S"]["1000"]["train"]), 3) for f in bp) in README
    assert " / ".join(_vz(median(bp[f]["suche"]["EA-S"]["1000"]["test"]), 3) for f in bp) in README
    # Training von PR2 mit der Zuordnung der Gitter (64 und 1 024 Auswertungen) wie in der README
    assert "64 Auswertungen " + " / ".join(_vz(median(bp[f]["pr2"]["8"]["train"]), 3) for f in bp) in README
    assert "1 024 Auswertungen " + " / ".join(_vz(median(bp[f]["pr2"]["32"]["train"]), 3) for f in bp) in README


def test_pr2_schwellenfall_breit_gestreut_1024():
    """Der Median liegt knapp unter der Schwelle 0,2, alle 20 Läufe sind schlechter als Best Fit: „gleich“ ist ein Schwellenartefakt und steht so in der README."""
    x = GEG["bin_packing"]["stark"]["pr2"]["32"]["test"]
    med = float(median(x))
    assert 0.19985 < med < 0.2 and _vz(med, 4) == "+0,1999"
    assert sum(v > 0 for v in x) == len(x) == 20
    assert _packen_urteil(x) == "gleich"
    assert "(Median +0,1999 bei 1 024 Auswertungen, in 20 von 20 Läufen schlechter)" in README and "knapp unter der Schwelle 0,2" in README
    assert [float(median(GEG["bin_packing"]["stark"]["pr2"][g]["test"])) for g in ("8", "16", "32")] == sorted(float(median(GEG["bin_packing"]["stark"]["pr2"][g]["test"])) for g in ("8", "16", "32"))   # steigt mit dem Gitter


def test_kernfrage_zahlen_rekord_zu_rekord_gross_und_late_acceptance():
    """Die Kernfrage nennt auch Rekord-zu-Rekord mit großem Budget und Late Acceptance mit großem Budget, nicht nur das kleine Budget."""
    rr_hi = [_lohnt_zellen("rr", "mix", k, "hi")[0] for k in (1, 3, 10, 30)]
    la_hi = [_lohnt_zellen("la", "mix", k, "hi")[0] for k in (1, 3, 10, 30)]
    la_lo = [_lohnt_zellen("la", "mix", k, "lo")[0] for k in (1, 3, 10, 30)]
    rr_lo = [_lohnt_zellen("rr", "mix", k, "lo")[0] for k in (1, 3, 10, 30)]
    assert rr_hi == [4, 3, 3, 1] and max(la_hi) == 2 and max(la_lo) == 0 and rr_lo[0] == 5 and max(rr_lo) == 5
    assert "(K = 1: 5 von 6 Zellen); unter Rekord-zu-Rekord mit großem Budget lohnte es sich in 4 / 3 / 3 / 1 von 6 Zellen (K = 1 / 3 / 10 / 30)" in README
    assert "unter Late Acceptance mit kleinem Budget in keiner Zelle, mit großem Budget in höchstens 2 von 6" in README


def test_hook_kleinstes_n_stern_late_acceptance_klein():
    """Kleinster Break-even im Mittel der Wiederholungen unter Late Acceptance, 50·n: Aufzählung ganzer Zahlen, numpy; liegt über N = 30."""
    best = None
    for k in (1, 3, 10, 30):
        for zn in H5["meta"]["zellen"]:
            kurve = H5["kurve"]["la"][zn]
            ki = C.H5_KS.index(k)
            q = float(np.mean([H5["mix"]["la"][zn][w][ki][0] for w in range(5)]))
            if q >= _qf(kurve, 1):
                continue
            s = _stern_enum(kurve, q, 1, k)
            if s is not None and (best is None or s < best[0]):
                best = (s, k, zn)
    assert best == (33, 1, "gleich/60")                                    # ganzzahlig aufgerundet; die App zeigt 32,4
    wert = F.stern("la", "gleich/60", "mix", 1, "lo")["wert"]
    assert 32 < wert <= 33 and wert > 30
    assert "kleinstes N* im Mittel der Wiederholungen 32,4 Instanzen bei K = 1 in gleich/60" in README


def test_gp_gegen_atc_besser_nur_im_regime_gross_und_schlechter_zaehlung():
    for g, schlechter in ((11, 3),):
        urteile = {}
        for regime in C.EP_REGIME:
            for fam in C.EP_FAMILIEN:
                e = GEG["einplanung"][f"{regime}|{fam}"]
                urteile[(regime, fam)] = _d1_scipy([x - y for x, y in zip(e["gp"]["16000"]["reue"], e["atc"][str(g)]["reue"])])
        assert {r for (r, _), u in urteile.items() if u == "besser"} == {"gross"}
        assert list(urteile.values()).count("besser") == 2
        assert list(urteile.values()).count("schlechter") == schlechter
    assert "in 2 von 8 Zellen besser (alle im Regime groß), in 3 schlechter" in README
    assert "(das 99,4-Fache bei 161 Werten)" in README
    assert "Vormessung 1 / 4 / 3; für 81 Werte 1 / 3 / 4" in README and "1 / 4 / 3 bei 11, 41 und 161 Werten, 1 / 3 / 4 bei 81" in README


def test_vormessung_raster_81_steht_so_im_plan_falls_vorhanden():
    bau = ROOT.parent / "hyperheuristiken-planung" / "BAU_9.md"
    if not bau.exists():
        pytest.skip("Planungsordner nicht vorhanden")
    assert "1 / 4 / 3 für 11, 41, 161 und 1 / 3 / 4 für 81" in bau.read_text(encoding="utf-8")


def test_verteilungswechsel_packen_familienwechsel_falls_vorhanden():
    quelle = ROOT.parent / "regel-verteilungswechsel-demo" / "rvw_tabellen.json"
    if not quelle.exists():
        pytest.skip("Nachbarordner nicht vorhanden (CI)")
    alles = json.loads(quelle.read_text(encoding="utf-8"))
    d = alles["packen"]
    assert d["baum_und_schablone"]["zaehlung"]["fremd"] == [0, 17, 13]                       # besser / gleich / schlechter
    assert len(d["baum_und_schablone"]["verfahren"]) == 5 and alles["meta"]["packen"]["auswertungen_suche"] == 1000
    assert "13 von 30 Zellen schlechter als Best Fit, 17 gleich, 0 besser" in README


def test_streuung_und_rundung_von_n_stern():
    """Die Streuung über die Wiederholungen übersteigt den Faktor 3; das Runden von Q_M auf zwei Stellen verschiebt N* höchstens um das 1,17-Fache (nicht um den Faktor 3)."""
    je = F.sterne_je_wdh("rr", "gleich/30", "mix", 3, "lo")
    w = [s["wert"] for s in je]
    assert f"{min(w):.1f}".replace(".", ",") == "15,3" and f"{max(w):.1f}".replace(".", ",") == "52,9" and max(w) / min(w) > 3
    je1 = [s["wert"] for s in F.sterne_je_wdh("rr", "gleich/30", "mix", 1, "lo")]
    assert f"{min(je1):.1f}".replace(".", ",") == "4,6" and f"{max(je1):.1f}".replace(".", ",") == "74,2" and max(je1) / min(je1) > 16
    assert "15,3 bis 52,9; K = 1: 4,6 bis 74,2, mehr als das 16-Fache" in README
    schlimmster = 1.0
    for akz in C.H5_AKZ:
        for zn in H5["meta"]["zellen"]:
            for stufe in C.STUFEN:
                b = 1 if stufe == "lo" else 4
                for art, k in (("mix", 1), ("mix", 3), ("mix", 10), ("mix", 30), ("einzel", 3)):
                    ki = C.H5_KS.index(k)
                    e = k * (1 if art == "mix" else 8)
                    kurve = H5["kurve"][akz][zn]
                    if art == "mix":
                        q = float(np.mean([H5["mix"][akz][zn][w][ki][0 if stufe == "lo" else 1] for w in range(5)]))
                    else:
                        q = float(np.mean([H5["einzel_alle"][akz][zn][stufe][H5["einzel"][akz][zn][w][ki]] for w in range(5)]))
                    s0 = _stern_stetig(kurve, q, b, e)
                    s1 = _stern_stetig(kurve, round(q, 2), b, e)
                    if s0 is not None and s1 is not None:
                        schlimmster = max(schlimmster, s0 / s1, s1 / s0)
    assert 1.16 < schlimmster < 1.17
    assert "höchstens um das 1,17-Fache" in README


def _stern_stetig(kurve, q, b, e):
    """N* = e / (β* − b) mit Q_F(β*) = q, β* per Bisektion auf ln β (numpy-Kurve, anderer Rechenweg als mek_breakeven); None ohne Gewinn oder über der Kurve."""
    if q >= _qf(kurve, b) or q < kurve[-1]:
        return None
    lo, hi = math.log(b), math.log(M[-1])
    for _ in range(200):
        mid = (lo + hi) / 2
        if _qf(kurve, math.exp(mid)) > q:
            lo = mid
        else:
            hi = mid
    beta = math.exp(hi)
    return e / (beta - b) if beta - b > 1e-9 else None


def test_auswertungen_gesamt_ist_nominal_und_steht_gerundet_in_der_readme():
    gesamt = H5["meta"]["auswertungen_gesamt"]
    assert gesamt == 619_650_000 and "rund 620 Millionen Auswertungen nach den Budgets gerechnet, nicht gezählt" in README


def test_karte_zeilen():
    karte = F.karte()["zeilen"]
    ids = [r["id"] for r in karte]
    assert len(ids) == len(set(ids)) and f"{len(karte)} Zeilen" in README
    nicht = [r for r in karte if r["art"] == "nicht_gemessen"]
    assert f"davon {len(nicht)} „nicht gemessen“" in README
    for r in karte:
        assert r["regel"] and r["einheit"] and r["voraussetzung"] and r["quelle"] and r["datum"]
        if r["art"] == "bgs":
            assert r["b"] + r["g"] + r["s"] == r["m"]
        if r["art"] == "lohnt":
            assert 0 <= r["k"] <= r["m"] and r["m"] == 6
        assert "lohnt nicht" not in json.dumps(r, ensure_ascii=False)               # keine Zeile sagt „lohnt nicht“ ohne Zahl
        if r["id"].startswith("rt-offline-"):
            _, _, akz, stufe, rest = r["id"].split("-")
            art, k = ("einzel", int(rest[6:])) if rest.startswith("einzel") else ("mix", int(rest[3:]))
            assert (r["k"], r["k_mittel"]) == _lohnt_zellen(akz, art, k, stufe)
        if r["art"] != "nicht_gemessen" and r["fahrzeug"] == "Einplanung":                                              # zwei Regeln, nie in einer Zählung gemischt
            assert "D1" in r["regel"]
        if r["art"] != "nicht_gemessen" and r["fahrzeug"] == "Bin Packing":
            assert r["regel"].startswith("Packen")
    for ident, soll in (("ep-wechsel-fam-16000", (0, 18, 54)), ("bp-menge-EA-S-orakel", (3, 0, 0)), ("bp-menge-EA-S-merkmal", (0, 0, 3))):
        r = next(x for x in karte if x["id"] == ident)
        assert (r["b"], r["g"], r["s"]) == soll
    assert "54 von 72 Zellen schlechter, 18 gleich, 0 besser" in README


def test_assumptions_text_ist_in_der_readme():
    assert TX.ASSUMPTIONS_MARKDOWN.strip() in README


def test_testzahl_der_readme_stimmt_mit_der_suite():
    m = re.search(r"\n(\d+) Tests\. Zusammensetzung", README)
    assert m, "Testzahl fehlt in der README"
    if os.environ.get("MEK_ZAEHLUNG"):
        pytest.skip("läuft schon in der Zählung")
    env = dict(os.environ, MEK_ZAEHLUNG="1")
    out = subprocess.run([sys.executable, "-X", "utf8", "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", str(ROOT / "tests")], capture_output=True, text=True,
                         stdin=subprocess.DEVNULL, env=env)
    assert len([z for z in out.stdout.splitlines() if "::" in z]) == int(m.group(1))


def test_keine_verbotenen_formulierungen():
    text = README.replace("Konfiguration", "")
    for wort in ("Saatwert", "Schwanz", "trägt", "Parameterwahl", "Verfahrenswahl", "Wahlregeln", "läuft lokal"):
        assert wort not in text, wort


def test_readme_ist_aktuell():
    out = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "tools" / "mek_readme.py"), "--check"], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    assert out.returncode == 0, out.stdout + out.stderr
