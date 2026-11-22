"""Training der Auswahl (mek_train): Mini-Instanz von Hand, Bitgleichheit der Zufallsauswahl, Gewichte, Zählung der Auswertungen mit unabhängigem Zähler."""

import pytest

import mek_constants as C
import mek_scenario as S
import mek_search as SR
import mek_train as T
from mek_rngblock import BlockSplitMix64


def test_gewichte_von_hand():
    p = T.gewichte([0.0, 4.0, 2.0, 0.0], [10, 10, 10, 10])
    # mittlere Belohnung 0, 0,4, 0,2, 0 → normiert 0, 2/3, 1/3, 0 → Untergrenze 0,02 → neu normiert
    roh = [0.02, 2 / 3, 1 / 3, 0.02]
    s = sum(roh)
    assert p == pytest.approx([x / s for x in roh]) and sum(p) == pytest.approx(1.0) and min(p) > 0.0
    assert T.gewichte([0.0, 0.0, 0.0], [5, 5, 5]) == [1 / 3] * 3                 # ohne jede Belohnung gleichverteilt
    assert T.gewichte([0.0, 3.0], [0, 3]) == pytest.approx([0.02 / 1.02, 1 / 1.02])    # eine Zugart ohne Anwendung hat Gewicht 0 und bekommt die Untergrenze


def test_mix_selector_zieht_nach_gewichten():
    sel = T.MixSelector([0.25, 0.25, 0.5])
    class R:                                                                    # feste Gleichverteilte
        def __init__(self, u): self.u = u
        def random(self): return self.u
    assert [sel.choose(R(u)) for u in (0.0, 0.2499, 0.25, 0.4999, 0.5, 0.9999)] == [0, 0, 1, 1, 2, 2]


def test_zufallsauswahl_ist_bitgleich_zur_eingebauten():
    _, D = T.instance("gleich", 30, 0)
    t0 = S.start_tour(D, "gleich", 30, 0, 0)
    a = SR.run_search(D, t0, 3000, C.ALLE_ZUGARTEN, "rr", BlockSplitMix64(S.run_seed("gleich", 30, 0, 0)))
    sel = T.TrainSelector(C.K, S.tour_cost(D, t0) / 30)
    b = SR.run_search(D, t0, 3000, C.ALLE_ZUGARTEN, "rr", BlockSplitMix64(S.run_seed("gleich", 30, 0, 0)), selector=sel)
    assert a["best"] == b["best"] and a["apps"] == b["apps"] and a["evals"] == b["evals"]
    assert sum(sel.anwendungen) == a["steps"] and all(x >= 0.0 for x in sel.summe)


def test_eine_einzelheuristik_ohne_zufallszahl_und_trainingskosten():
    verh = T.train_instance("gleich", 30, 1000, "rr")[2]
    assert len(verh) == C.K and all(0.5 < v <= 1.0 for v in verh)
    p, h = T.trainiere("gleich", 30, [1000, 1001], "rr")
    assert h in (2, 3, 7) and sum(p) == pytest.approx(1.0) and min(p) > 0.0     # 2-opt-Familie vorn (Stück 1)


def test_training_ist_deterministisch_und_aendert_sich_mit_der_instanz():
    a = T.trainiere("gleich", 30, [1000], "rr", einzel=False)
    assert a == T.trainiere("gleich", 30, [1000], "rr", einzel=False)
    assert a != T.trainiere("gleich", 30, [1001], "rr", einzel=False)


def test_trainingsinstanzen_der_wiederholungen():
    assert T.training_instanzen(0, 3) == [1000, 1001, 1002] and T.training_instanzen(2, 2) == [1060, 1061]
    assert set(T.training_instanzen(4, 30)).isdisjoint(range(30))              # Trainings- und Testinstanzen sind getrennt
