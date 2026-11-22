"""Training der Auswahl auf der Rundtour: gelernte Mischung und gelernte Einzelheuristik, Einsatz auf frischen Instanzen.

Gelernte Mischung: ein Lauf mit Zufallsauswahl über alle acht Zugarten auf einer Trainingsinstanz mit der Standardbelohnung (mek_select); das Gewicht
einer Zugart ist ihre mittlere Belohnung je Anwendung, die Gewichte werden normiert und auf mindestens 0,02 gehoben. Kosten: ein Lauf von ℓ = 50·n
Auswertungen je Trainingsinstanz. Gelernte Einzelheuristik: alle acht Zugarten einzeln je Trainingsinstanz (8 Läufe), die mit dem kleinsten mittleren
Verhältnis Endwert zu Startwert gewinnt. Zufall nur über SplitMix64 (mek_rng, blockweise mek_rngblock)."""

from functools import lru_cache

import mek_constants as C
import mek_scenario as S
import mek_select as SE
from mek_rngblock import BlockSplitMix64
from mek_search import run_search


@lru_cache(maxsize=512)
def instance(familie: str, n: int, idx: int):
    """(Punkte, Abstandsmatrix) der Instanz; idx 0 bis 29 sind die Testinstanzen, ab 1000 die Trainingsinstanzen."""
    return S.make_instance(familie, n, idx)


class TrainSelector:
    """Zufallsauswahl über m Arme, die nebenbei die Standardbelohnung je Arm aufsummiert (für die Gewichte der gelernten Mischung).

    `choose` ist bitgleich zur eingebauten Zufallsauswahl der Suche (int(u·m))."""

    def __init__(self, m: int, kante: float):
        self.m = m
        self.kante = kante
        self.summe = [0.0] * m
        self.anwendungen = [0] * m

    def choose(self, rng) -> int:
        return int(rng.random() * self.m)

    def update(self, index: int, delta: float, kosten: int, angenommen: bool) -> None:
        self.summe[index] += SE.reward_standard(delta, kosten, self.kante)
        self.anwendungen[index] += 1


class MixSelector:
    """Feste Mischung: zieht die Zugart nach den Gewichten p (eine Zufallszahl je Anwendung, kumulierte Summe)."""

    def __init__(self, p):
        self.p = list(p)

    def choose(self, rng) -> int:
        u = rng.random()
        c = 0.0
        for j, pj in enumerate(self.p):
            c += pj
            if u < c:
                return j
        return len(self.p) - 1

    def update(self, index: int, delta: float, kosten: int, angenommen: bool) -> None:
        """Die feste Mischung lernt nichts."""


def gewichte(summe, anwendungen):
    """Gewicht je Zugart = mittlere Belohnung je Anwendung, normiert, Untergrenze 0,02 (dann neu normiert); ohne jede Belohnung gleichverteilt."""
    m = len(summe)
    w = [s / max(a, 1) for s, a in zip(summe, anwendungen)]
    tot = sum(w)
    if tot <= 0:
        return [1.0 / m] * m
    p = [max(x / tot, C.P_BODEN) for x in w]
    tot = sum(p)
    return [x / tot for x in p]


def lauf(familie: str, n: int, idx: int, run: int, arms, akz: str, budget: int, selector=None, checkpoints=()):
    """Ein Lauf: Starttour und Zufallsstrom hängen nur an (Familie, n, Instanz, Lauf); alle Varianten eines Laufs lesen denselben Strom von vorn."""
    _, D = instance(familie, n, idx)
    t0 = S.start_tour(D, familie, n, idx, run)
    rng = BlockSplitMix64(S.run_seed(familie, n, idx, run))
    return run_search(D, t0, budget, tuple(arms), akz, rng, checkpoints=checkpoints, selector=selector), S.tour_cost(D, t0)


def train_stream(familie: str, n: int, idx: int, nummer: int) -> BlockSplitMix64:
    """Strom des Trainings (Zweck 44): nummer 0 die Zufallsauswahl, 1 + h die Einzelheuristik h."""
    return BlockSplitMix64(S.derive(C.H5_TRAIN_SEED_ZWECK, C.FAMILIEN.index(familie), n, idx, nummer))


def train_instance(familie: str, n: int, idx: int, akz: str, einzel: bool = True):
    """Training auf einer Instanz: (Summe der Belohnungen je Zugart, Anwendungen je Zugart, Verhältnisse Endwert / Start je Einzelheuristik oder None).

    Kostet ℓ = 50·n Auswertungen für die Mischung und 8·ℓ für die Einzelheuristiken."""
    _, D = instance(familie, n, idx)
    t0 = S.start_tour(D, familie, n, idx, 0)
    c0 = S.tour_cost(D, t0)
    lo = C.LO_F * n
    sel = TrainSelector(C.K, c0 / n)
    run_search(D, t0, lo, C.ALLE_ZUGARTEN, akz, train_stream(familie, n, idx, 0), selector=sel)
    verh = None
    if einzel:
        verh = []
        for h in range(C.K):
            r = run_search(D, t0, lo, (h,), akz, train_stream(familie, n, idx, 1 + h))
            verh.append(r["best"] / c0)
    return sel.summe, sel.anwendungen, verh


def trainiere(familie: str, n: int, idxs, akz: str, einzel: bool = True):
    """Training auf den Instanzen `idxs`: (Gewichte p der Mischung, Index der besten Einzelheuristik oder None)."""
    summe = [0.0] * C.K
    anw = [0] * C.K
    verh = [[] for _ in range(C.K)]
    for idx in idxs:
        s, a, v = train_instance(familie, n, idx, akz, einzel)
        summe = [x + y for x, y in zip(summe, s)]
        anw = [x + y for x, y in zip(anw, a)]
        if einzel:
            for h in range(C.K):
                verh[h].append(v[h])
    p = gewichte(summe, anw)
    beste = None
    if einzel:
        mittel = [sum(v) / len(v) for v in verh]
        beste = min(range(C.K), key=lambda h: (mittel[h], h))
    return p, beste


def training_instanzen(wdh: int, k: int) -> list[int]:
    """Trainingsinstanzen der Wiederholung `wdh`: 1000 + 30·wdh + 0 bis k - 1."""
    return [C.H5_TRAIN_OFFSET + 30 * wdh + j for j in range(k)]
