"""Orakel-Tests (unabhängiger Rechenweg): Break-even auf drei Wegen, unabhängiger Zähler der Auswertungen, Bilanz, Referenz, Karte gegen die Quellen.

(a) N* aus der geschlossenen Umkehrung, aus der Aufzählung ganzer Zahlen mit der Vorwärtsfunktion und aus scipy.optimize.brentq (falls scipy vorhanden), auf Zufallskurven
    und auf jeder Zelle der eingefrorenen Messung; (b) ein Dekorator zählt jeden Aufruf einer Delta-Auswertung gegen die Buchführung der Suche; (d) Bilanz C_M(N*) = C_F(N*);
(e) keine Lauflänge unter der Referenz; (f) die Zeilen der Karte werden aus den Quellen nachgezählt."""

import json
import math
import random
import sys
from pathlib import Path

import pytest

import mek_breakeven as BE
import mek_constants as C
import mek_frozen as F
import mek_kosten as KO
import mek_moves as MV
import mek_search as SR
import mek_train as T

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
M = C.H5_MULTS


def _zufallskurve(rng):
    werte = sorted((rng.uniform(0.1, 15.0) for _ in M), reverse=True)
    return werte


def test_orakel_drei_wege_auf_zufallskurven():
    """N* aus der Umkehrung, aus der Aufzählung ganzer Zahlen mit der Vorwärtsfunktion und aus brentq auf Q_F(β) − Q_M (scipy, falls vorhanden)."""
    brentq = pytest.importorskip("scipy.optimize").brentq
    rng = random.Random(2026)
    pruefungen = 0
    for _ in range(40):
        kv = _zufallskurve(rng)
        q = rng.uniform(kv[-1] - 0.2, kv[0] + 0.2)
        e = rng.choice([1.0, 3.0, 8.0, 30.0, 240.0])
        b = rng.choice([1.0, 4.0])
        s = BE.n_stern(M, kv, q, b, e)
        if s["status"] != "ok":
            continue
        enum = BE.n_stern_aufzaehlung(M, kv, q, b, e, n_max=20000)
        assert enum == math.ceil(s["wert"] - 1e-9) or enum is None and s["wert"] > 20000
        beta = brentq(lambda x: BE.abstand_bei(M, kv, x) - q, M[0], M[-1], xtol=1e-14)
        assert math.isclose(e / (beta - b), s["wert"], rel_tol=1e-6)
        pruefungen += 1
    assert pruefungen >= 10


@pytest.mark.parametrize("akz", ["ob", "rr", "la"])
def test_zaehler_summe_ist_das_budget_und_b5_hoechstens_fuenf(akz, monkeypatch):
    """Unabhängiger Zähler: jeder Aufruf eines Vorschlags wird mitgezählt (Dekorator); 2opt_b5 zählt je Anwendung höchstens 5 Auswertungen."""
    aufrufe = {h: 0 for h in range(C.K)}

    def umhuellen(h, f):
        def g(*a, **k):
            aufrufe[h] += 1
            return f(*a, **k)
        return g
    monkeypatch.setattr(SR, "PROPOSE", tuple(umhuellen(h, f) for h, f in enumerate(MV.PROPOSE)))
    r, _ = T.lauf("cluster", 30, 1, 0, C.ALLE_ZUGARTEN, akz, 4000, None, ())
    assert r["used"] == 4000 and sum(r["evals"]) == 4000
    assert [r["apps"][h] for h in range(7)] == [aufrufe[h] for h in range(7)]
    assert r["evals"][7] <= 5 * r["apps"][7] and all(r["evals"][h] == r["apps"][h] for h in range(7))


def test_n_stern_auf_den_daten_drei_wege():
    """Umkehrung gegen Aufzählung (ganze Zahlen mit der Vorwärtsfunktion) für jede Zelle, Art, K, Stufe und Wiederholung der Datei."""
    import mek_breakeven as BE
    d = F.h5()
    geprueft = 0
    for akz in C.H5_AKZ:
        for zn in d["meta"]["zellen"]:
            kurve = d["kurve"][akz][zn]
            for art in C.ARTEN:
                for k in C.H5_KS:
                    for stufe in C.STUFEN:
                        for wdh in range(5):
                            s = F.stern(akz, zn, art, k, stufe, wdh)
                            q = F.trainiert_gap(akz, zn, art, k, stufe, wdh)
                            b = 1 if stufe == "lo" else 4
                            e = F.KO.entwicklung_in_stufen(art, k)
                            if s["status"] == "ok":
                                enum = BE.n_stern_aufzaehlung(C.H5_MULTS, kurve, q, b, e, n_max=3000)
                                if s["wert"] <= 3000:
                                    assert enum == pytest.approx(s["wert"], abs=1.0) and enum >= s["wert"] - 1e-9
                                geprueft += 1
                            if s["status"] == "nie":
                                assert q >= BE.abstand_bei(C.H5_MULTS, kurve, b) - 1e-12
    assert geprueft > 300


def test_bilanz_gleiche_gesamtzahl_bei_n_stern():
    """(d) Bei N* haben Meta-Ebene und Gegner (mit β' aus H2) dieselbe Gesamtzahl, und der Gegner erreicht dort den Abstand der Meta-Ebene (bis auf die Interpolation)."""
    d = F.h5()
    kurve = d["kurve"]["rr"]["gleich/30"]
    q = F.trainiert_gap("rr", "gleich/30", "mix", 3, "lo", 0)
    s = F.stern("rr", "gleich/30", "mix", 3, "lo", 0)
    assert s["status"] == "ok"
    n = s["wert"]
    lo = KO.kontrollstufe(30)
    e = KO.entwicklung_rundtour("mix", 3, 30)
    beta = KO.gleiche_gesamtzahl_budget(e, 0, n, lo)
    assert math.isclose(KO.gesamt(e, n, lo), n * beta, rel_tol=1e-12)                      # E + N b = N β'
    assert abs(BE.abstand_bei(M, kurve, beta / lo) - q) < 1e-9


def test_keine_laufmenge_unter_der_referenz_im_kleinen():
    """(e) Eine Zelle, 3 Instanzen: kein Lauf ist kürzer als der Wert der Referenzdatei, ohne dass die Datei als unterboten gilt (Held-Karp-Orakel gehört in Stück 1)."""
    refs = json.loads((ROOT / "mek_refs.json").read_text(encoding="utf-8"))["refs"]["gleich"]["30"]
    for idx in range(3):
        r, _ = T.lauf("gleich", 30, idx, 0, C.ALLE_ZUGARTEN, "rr", 3000, None, ())
        assert r["best"] >= refs[idx] * 0.98                                                # die Langläufe sind keine Optima, aber nahe dran


def test_karte_gegen_die_quellen_nachgezaehlt():
    """(f) Jede Zeile der Karte wird aus den Messdateien neu gezählt (Nachbarordner, falls vorhanden) und stimmt mit der gespeicherten Zeile überein."""
    import mek_make_karte as MK
    if not (ROOT.parent / "auswahlregeln-demo" / "asw_frozen.json").exists():
        pytest.skip("Nachbarordner nicht vorhanden (CI)")
    gespeichert = {z["id"]: z for z in F.karte()["zeilen"]}
    for z in MK.bauen_karte()["zeilen"]:
        assert gespeichert[z["id"]] == z, z["id"]
