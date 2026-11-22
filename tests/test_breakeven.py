"""Break-even: Handbeispiele von Hand, Orakel auf drei Wegen, Eigenschaften und Randfälle (reine Funktionen, keine Messdaten).

Einheiten wie in der Vormessung: Budgets und Entwicklungskosten in Vielfachen von ℓ = 50·n Auswertungen. Die Kurven der Handbeispiele sind Auszüge der Rohausgaben der Vormessung
(Rundung auf zwei Stellen), die Erwartungswerte stehen als Rechnung im Test."""

import math
import random
from fractions import Fraction as Fr

import mek_breakeven as BE
import mek_constants as C

M = C.H5_MULTS
KURVE = {
    ("gleich", 30, "rr"): [5.19, 3.57, 2.89, 2.15, 1.76, 1.24, 0.91, 0.72, 0.70, 0.61, 0.52],
    ("gleich", 60, "la"): [13.56, 11.03, 8.84, 6.52, 5.27, 4.17, 3.87, 3.27, 2.91, 2.60, 2.46],
    ("cluster", 60, "rr"): [10.40, 8.37, 7.08, 5.29, 4.20, 3.02, 2.39, 1.78, 1.48, 1.12, 0.94],
    ("gitter", 30, "rr"): [4.83, 3.71, 3.15, 2.42, 1.97, 1.54, 1.29, 1.07, 0.94, 0.73, 0.66],
    ("gleich", 30, "la"): [7.80, 5.87, 4.19, 2.74, 2.16, 1.86, 1.59, 1.39, 1.33, 1.23, 1.22],
}


def test_handbeispiel_gleich_30_rekord_zu_rekord_k1():
    kv = KURVE[("gleich", 30, "rr")]
    q = 4.52
    anteil = (kv[0] - q) / (kv[0] - kv[1])
    assert abs(anteil - 0.4136) < 5e-4                                   # (5,19 - 4,52) / (5,19 - 3,57)
    beta = math.exp(anteil * math.log(1.5))
    assert abs(beta - 1.1826) < 5e-4                                     # B* = 1,5^0,4136 ℓ
    s = BE.n_stern(M, kv, q, 1.0, 1.0)
    assert s["status"] == "ok" and abs(s["wert"] - 1.0 / (beta - 1.0)) < 1e-9 and abs(s["wert"] - 5.4773) < 1e-3
    assert abs(round(s["wert"], 1) - 5.5) < 1e-12
    # Gegenprobe: mit β' = (1 + 1/N*) ℓ hat der Gegner genau den Abstand der Meta-Ebene
    assert abs(BE.abstand_bei(M, kv, BE.gegner_budget(1.0, 1.0, s["wert"])) - q) < 1e-9
    # Gesamtzahlen bei N = 30 (n = 30, ℓ = 1 500): 1 500 + 30·1 500 = 30·1 550 für den Gegner
    assert 1500 + 30 * 1500 == 46_500 and Fr(30 * 1500) * (1 + Fr(1, 30)) == 46_500 and Fr(1500) * (1 + Fr(1, 30)) == 1550
    assert BE.abstand_bei(M, kv, 1 + 1 / 30) > q and BE.abstand_bei(M, kv, 1 + 1 / 5) < q


def test_weitere_handwerte():
    s = BE.n_stern(M, KURVE[("gleich", 60, "la")], 11.94, 1.0, 24.0)
    assert s["status"] == "ok" and abs(s["wert"] - 80.96) < 0.05 and abs(s["wert"] - 80.8) < 0.3     # Einzelheuristik K = 3
    s = BE.n_stern(M, KURVE[("gleich", 30, "la")], 8.43, 1.0, 1.0)
    assert s["status"] == "nie" and s["wert"] is None                                                  # 8,43 % gegen 7,80 %
    s = BE.n_stern(M, KURVE[("cluster", 60, "rr")], 3.83, 4.0, 1.0)
    assert s["status"] == "ok" and abs(s["wert"] - 1.84) < 0.02                                         # großes Budget
    s = BE.n_stern(M, KURVE[("gleich", 30, "rr")], 0.40, 1.0, 1.0)
    assert s["status"] == "ueber_kurve" and s["wert"] is None                                           # 0,40 % unter 0,52 %


def test_lebensdauer_ist_genau_n_stern():
    kv = KURVE[("gleich", 30, "rr")]
    for r, lohnt in ((6, True), (5, False)):
        assert (BE.abstand_bei(M, kv, 1.0 + 1.0 / r) >= 4.52) == lohnt


def test_empfindlichkeit_bei_kleinem_gewinn():
    erg = []
    for dg in (-0.005, 0.005):
        for dr in (-0.005, 0.005):
            for dc in (-0.005, 0.005):
                kv = list(KURVE[("gitter", 30, "rr")])
                kv[0] += dr
                kv[1] += dc
                s = BE.n_stern(M, kv, 4.81 + dg, 1.0, 3.0)
                assert s["status"] == "ok"
                erg.append(s["wert"])
    assert min(erg) < 326.9 < max(erg) and max(erg) / min(erg) > 2.9      # Handfall (Ecken der Rundung, kleiner Gewinn): Faktor 3; in den Daten der Demo höchstens 1,17 (test_claims)


def test_plateau_gibt_nie_nie_eine_zahl():
    kv = [3.0] * len(M)
    assert BE.n_stern(M, kv, 3.0, 1.0, 5.0)["status"] == "nie"
    assert BE.n_stern(M, kv, 2.0, 1.0, 5.0)["status"] == "ueber_kurve"
    assert abs(BE.budget_fuer_abstand(M, [5.0, 4.0, 4.0, 3.0] + [2.0] * 7, 4.0) - M[1]) < 1e-12           # zwei gleiche Stützstellen: die frühere


def test_randfaelle():
    kv = KURVE[("gleich", 30, "rr")]
    s = BE.n_stern(M, kv, 4.0, 1.0, 0.0)                                  # K = 0: E = 0, Gewinn
    assert s["status"] == "sofort" and s["wert"] == 0.0 and BE.lohnt(s, 1)
    assert BE.n_stern(M, kv, BE.abstand_bei(M, kv, 1.0), 1.0, 3.0)["status"] == "nie"   # genau gleich
    knapp = BE.n_stern(M, kv, BE.abstand_bei(M, kv, 1.0) - 1e-6, 1.0, 3.0)
    assert knapp["status"] == "ok" and knapp["wert"] > 1e5                # sehr groß, nicht nie
    assert BE.abstand_bei(M, kv, 0.5) == kv[0] and BE.abstand_bei(M, kv, 100) == kv[-1]  # nicht extrapoliert
    assert not BE.lohnt({"status": "nie", "wert": None}, 1e9) and not BE.lohnt({"status": "ueber_kurve", "wert": None}, 1e9)


def _zufallskurve(rng):
    return sorted((rng.uniform(0.1, 15.0) for _ in M), reverse=True)


def test_eigenschaften():
    rng = random.Random(7)
    for _ in range(40):
        kv = _zufallskurve(rng)
        q = rng.uniform(kv[-1], kv[0])
        b = 1.0
        if q >= BE.abstand_bei(M, kv, b):
            continue
        s1 = BE.n_stern(M, kv, q, b, 2.0)
        s2 = BE.n_stern(M, kv, q, b, 6.0)
        if s1["status"] == s2["status"] == "ok":
            assert s2["wert"] >= s1["wert"] - 1e-12                     # N* wächst mit E bei festem Q_M und Q_F
            assert math.isclose(s2["wert"] / s1["wert"], 3.0, rel_tol=1e-9)     # linear in E
        # „nie“ genau dann, wenn Q_M >= Q_F(b)
        assert (BE.n_stern(M, kv, q, b, 2.0)["status"] == "nie") == (q >= BE.abstand_bei(M, kv, b))
        # Skalierung der Einheit: ℓ in Vielfachen von ℓ oder doppelter Einheit, N* ändert sich nicht
        m2 = tuple(2 * x for x in M)
        s3 = BE.n_stern(m2, kv, q, 2 * b, 2 * 2.0)
        if s1["status"] == "ok":
            assert math.isclose(s3["wert"], s1["wert"], rel_tol=1e-9)


def test_lohnt_ist_monoton_in_n():
    kv = KURVE[("gleich", 30, "rr")]
    s = BE.n_stern(M, kv, 4.52, 1.0, 1.0)
    erg = [BE.lohnt(s, n) for n in (1, 2, 5, 5.47, 5.48, 6, 30, 2000)]
    assert erg == [False, False, False, False, True, True, True, True]
