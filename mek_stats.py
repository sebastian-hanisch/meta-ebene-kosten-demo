"""Entscheidungsregeln und Statistik für die Zählungen: Wilcoxon-Vorzeichen-Rang-Test (exakt), Regel D1 der Einplanung, Regel der Platzierungsfunktionen.

Zwei Entscheidungsregeln der Linie, nie in einer Zählung gemischt:
  D1 (Einplanung, Stück 5)     Differenzen der Reue (Anteil, 0,01 = ein Prozentpunkt): "besser", wenn mindestens 75 % der Läufe < 0, Median <= -0,01, p < 0,01
  Packen (Stück 6)             Differenzen des Überschusses in Prozentpunkten: "besser", wenn Median <= -0,2 und mindestens 15 von 20 Läufen < 0
Beide sind gesetzte Regeln, nicht abgeleitet."""

import math
from statistics import median

D1_ANTEIL, D1_MEDIAN, D1_P = 0.75, 0.01, 0.01
PACKEN_TOL, PACKEN_KMIN = 0.2, 15


def wilcoxon_exact(deltas) -> float:
    """Zweiseitiger p-Wert des Wilcoxon-Vorzeichen-Rang-Tests, exakt über alle 2^n Vorzeichenmuster (Nullen entfallen, Bindungen bekommen mittlere
    Ränge, hier als doppelte Ränge ganzzahlig gerechnet). Ohne Werte ungleich null: 1."""
    nz = [float(x) for x in deltas if x != 0]
    n = len(nz)
    if n == 0:
        return 1.0
    order = sorted(range(n), key=lambda i: abs(nz[i]))
    rank2 = [0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and abs(nz[order[j + 1]]) == abs(nz[order[i]]):
            j += 1
        for q in range(i, j + 1):
            rank2[order[q]] = (i + 1) + (j + 1)
        i = j + 1
    total = sum(rank2)
    counts = [0] * (total + 1)
    counts[0] = 1
    for r in rank2:
        for s in range(total, r - 1, -1):
            counts[s] += counts[s - r]
    w_plus = sum(r for r, x in zip(rank2, nz) if x > 0)
    denom = 2 ** n
    lower = sum(counts[: w_plus + 1]) / denom
    upper = sum(counts[w_plus:]) / denom
    return min(1.0, 2.0 * min(lower, upper))


def d1_urteil(deltas) -> dict:
    """Regel D1 für gepaarte Differenzen Delta = Reue(Regel) - Reue(Gegner) als Anteil: besser / gleich / schlechter (spiegelbildlich)."""
    deltas = [float(x) for x in deltas]
    if not deltas:
        return {"urteil": "keine Daten", "anteil_neg": 0.0, "anteil_pos": 0.0, "median": 0.0, "p": 1.0, "n": 0}
    n = len(deltas)
    neg = sum(x < 0 for x in deltas) / n
    pos = sum(x > 0 for x in deltas) / n
    med = float(median(deltas))
    p = wilcoxon_exact(deltas)
    if neg >= D1_ANTEIL and med <= -D1_MEDIAN and p < D1_P:
        urteil = "besser"
    elif pos >= D1_ANTEIL and med >= D1_MEDIAN and p < D1_P:
        urteil = "schlechter"
    else:
        urteil = "gleich"
    return {"urteil": urteil, "anteil_neg": neg, "anteil_pos": pos, "median": med, "p": p, "n": n}


def packen_urteil(deltas, tol: float = PACKEN_TOL, k_min: int = PACKEN_KMIN) -> dict:
    """Regel der Platzierungsfunktionen für Differenzen in Prozentpunkten Überschuss (negativ = besser als der Gegner)."""
    deltas = [float(x) for x in deltas]
    med = float(median(deltas))
    neg = sum(x < 0 for x in deltas)
    pos = sum(x > 0 for x in deltas)
    if med <= -tol and neg >= k_min:
        urteil = "besser"
    elif med >= tol and pos >= k_min:
        urteil = "schlechter"
    else:
        urteil = "gleich"
    return {"urteil": urteil, "median": med, "laeufe_neg": neg, "laeufe_pos": pos, "n": len(deltas)}


def zaehle(urteile) -> tuple[int, int, int]:
    """(besser, gleich, schlechter) einer Liste von Urteilen."""
    urteile = list(urteile)
    return urteile.count("besser"), urteile.count("gleich"), urteile.count("schlechter")


def mittel(werte) -> float:
    werte = list(werte)
    return sum(werte) / len(werte)


def standardfehler(werte) -> float:
    """Standardfehler des Mittels (Stichprobenabweichung durch Wurzel n); bei weniger als zwei Werten 0."""
    werte = list(werte)
    if len(werte) < 2:
        return 0.0
    m = mittel(werte)
    return math.sqrt(sum((x - m) ** 2 for x in werte) / (len(werte) - 1)) / math.sqrt(len(werte))
