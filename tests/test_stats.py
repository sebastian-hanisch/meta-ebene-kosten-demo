"""Entscheidungsregeln: exakter Wilcoxon-Test gegen scipy (falls vorhanden) und von Hand, Regel D1 und Regel der Platzierungsfunktionen an gesetzten Werten."""

import random

import pytest

import mek_stats as ST


def test_wilcoxon_von_hand():
    # n = 3, alle positiv: nur das Muster „alle +“ und „alle −“ liegen am Rand: p = 2 · 1/8
    assert ST.wilcoxon_exact([1.0, 2.0, 3.0]) == pytest.approx(0.25)
    assert ST.wilcoxon_exact([]) == 1.0 and ST.wilcoxon_exact([0.0, 0.0]) == 1.0
    assert ST.wilcoxon_exact([1.0, -1.0]) == 1.0
    # 20 gleich große positive Werte: p = 2 / 2^20 (kleinster möglicher Wert)
    assert ST.wilcoxon_exact([0.5] * 20) == pytest.approx(2 / 2 ** 20)


def test_wilcoxon_gegen_scipy():
    stats = pytest.importorskip("scipy.stats")
    rng = random.Random(3)
    for _ in range(40):
        n = rng.randint(5, 20)
        d = [rng.gauss(0.3, 1.0) for _ in range(n)]                      # keine Bindungen, keine Nullen: scipy rechnet exakt
        assert ST.wilcoxon_exact(d) == pytest.approx(float(stats.wilcoxon(d, method="exact").pvalue), rel=1e-9)


def test_d1():
    besser = [-0.05] * 16 + [0.01] * 4                                    # 80 % negativ, Median −0,05, p klein
    u = ST.d1_urteil(besser)
    assert u["urteil"] == "besser" and u["anteil_neg"] == 0.8 and u["median"] == -0.05 and u["p"] < 0.01
    assert ST.d1_urteil([-0.05] * 15 + [0.01] * 5)["urteil"] == "besser"   # genau 75 %
    assert ST.d1_urteil([-0.05] * 14 + [0.01] * 6)["urteil"] == "gleich"   # 70 %
    assert ST.d1_urteil([-0.0099] * 20)["urteil"] == "gleich"              # Median über −0,01
    assert ST.d1_urteil([-0.01] * 20)["urteil"] == "besser"                # Median genau −0,01 zählt
    assert ST.d1_urteil([0.05] * 20)["urteil"] == "schlechter"
    assert ST.d1_urteil([0.0] * 20)["urteil"] == "gleich" and ST.d1_urteil([])["urteil"] == "keine Daten"


def test_packen():
    assert ST.packen_urteil([-0.3] * 15 + [0.0] * 5)["urteil"] == "besser"
    assert ST.packen_urteil([-0.3] * 14 + [0.0] * 6)["urteil"] == "gleich"          # nur 14 von 20 unter null
    assert ST.packen_urteil([-0.19] * 20)["urteil"] == "gleich" and ST.packen_urteil([-0.2] * 20)["urteil"] == "besser"
    assert ST.packen_urteil([0.2] * 15 + [0.0] * 5)["urteil"] == "schlechter" and ST.packen_urteil([0.0] * 20)["urteil"] == "gleich"


def test_zaehlen_und_mittel():
    assert ST.zaehle(["besser", "gleich", "gleich", "schlechter"]) == (1, 2, 1)
    assert ST.mittel([1, 2, 3]) == 2 and ST.standardfehler([1.0]) == 0.0 and ST.standardfehler([1.0, 3.0]) == pytest.approx(1.0)
