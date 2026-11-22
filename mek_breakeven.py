"""Break-even der Meta-Ebene: ab wie vielen Instanzen zahlt sich Training plus Einsatz gegen einen festen Gegner mit gleicher Gesamtzahl aus?

Reine Funktionen ohne Streamlit. Die Gütekurve des Gegners Q_F(β) ist über Stützstellen β_i (Vielfache der Kontrollstufe ℓ) gegeben und zwischen
ihnen linear in ln β. Budgets und Entwicklungskosten stehen in Vielfachen von ℓ; N* ist dann eine reine Zahl von Instanzen.

    β'(N) = b_M + (E_M - e_F) / N          Budget je Instanz, das der Gegner bei gleicher Gesamtzahl ausgeben darf
    N*    = (E_M - e_F) / (β* - b_M)       mit Q_F(β*) = Q_M(b_M); "nie", wenn Q_M(b_M) >= Q_F(b_M); "ueber_kurve", wenn Q_M(b_M) < Q_F(letzte Stützstelle)
"""

import math

EPS_N = 1e-9


def abstand_bei(mults, kurve, beta: float) -> float:
    """Q_F(β): linear in ln β zwischen den Stützstellen; außerhalb des Bereichs der Wert der nächsten Stützstelle (nicht extrapoliert)."""
    if beta <= mults[0]:
        return float(kurve[0])
    if beta >= mults[-1]:
        return float(kurve[-1])
    for i in range(len(mults) - 1):
        if mults[i] <= beta <= mults[i + 1]:
            f = (math.log(beta) - math.log(mults[i])) / (math.log(mults[i + 1]) - math.log(mults[i]))
            return float(kurve[i] + f * (kurve[i + 1] - kurve[i]))
    raise AssertionError("unerreichbar")


def budget_fuer_abstand(mults, kurve, ziel: float):
    """Kleinstes β mit Q_F(β) = ziel (log-linear zwischen den Stützstellen); None, wenn die Kurve das Ziel nicht erreicht (ziel unter dem letzten Wert).

    Ist das Ziel schon bei der ersten Stützstelle erreicht (ziel >= Q_F(β_1)), ist β = β_1. Bei einem Plateau (zwei gleiche Werte) gilt die frühere Stützstelle."""
    if ziel >= kurve[0]:
        return float(mults[0])
    if ziel < kurve[-1]:
        return None
    for i in range(len(mults) - 1):
        if kurve[i] >= ziel >= kurve[i + 1]:
            if kurve[i] == kurve[i + 1]:
                return float(mults[i])
            f = (kurve[i] - ziel) / (kurve[i] - kurve[i + 1])
            return float(math.exp(math.log(mults[i]) + f * (math.log(mults[i + 1]) - math.log(mults[i]))))
    return None


def gegner_budget(b_m: float, e_m: float, n: float, e_f: float = 0.0) -> float:
    """β'(N) = b_M + (E_M - e_F) / N: was der Gegner je Instanz ausgeben darf, wenn beide insgesamt gleich viel Auswertungen haben."""
    return b_m + (e_m - e_f) / n


def n_stern(mults, kurve, q_m: float, b_m: float, e_m: float, e_f: float = 0.0) -> dict:
    """Break-even N* für eine Meta-Ebene mit Abstand q_m bei Einsatz b_m und Entwicklungskosten e_m (alles in Vielfachen von ℓ).

    Rückgabe: {"status": "ok" | "nie" | "ueber_kurve" | "sofort", "wert": N* als Zahl oder None, "beta_stern": β* oder None}.
    "sofort": keine Mehrkosten (e_m <= e_f) und Gewinn; "nie": kein Gewinn bei gleichem Einsatzbudget (q_m >= Q_F(b_m)); "ueber_kurve": der Gewinn ist größer,
    als die gemessene Kurve abdeckt (q_m unter dem Wert der letzten Stützstelle)."""
    if q_m >= abstand_bei(mults, kurve, b_m):
        return {"status": "nie", "wert": None, "beta_stern": None}
    if e_m <= e_f:
        return {"status": "sofort", "wert": 0.0, "beta_stern": None}
    beta = budget_fuer_abstand(mults, kurve, q_m)
    if beta is None:
        return {"status": "ueber_kurve", "wert": None, "beta_stern": None}
    extra = beta - b_m
    if extra <= EPS_N:
        return {"status": "nie", "wert": None, "beta_stern": beta}
    return {"status": "ok", "wert": (e_m - e_f) / extra, "beta_stern": beta}


def n_stern_aufzaehlung(mults, kurve, q_m: float, b_m: float, e_m: float, e_f: float = 0.0, n_max: int = 5000):
    """Orakel-Weg zu N*: kleinste ganze Zahl N in 1 .. n_max mit q_m <= Q_F(β'(N)); None, wenn es keine gibt (nur Vorwärtsfunktion, keine Umkehrung)."""
    for n in range(1, n_max + 1):
        if q_m <= abstand_bei(mults, kurve, gegner_budget(b_m, e_m, n, e_f)):
            return n
    return None


def lohnt(stern: dict, n: float) -> bool:
    """Lohnt sich die Meta-Ebene bei n Instanzen? Nur bei Status ok oder sofort und N* <= n."""
    return stern["status"] in ("ok", "sofort") and stern["wert"] <= n + EPS_N
