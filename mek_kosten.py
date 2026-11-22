"""Kostenbuch: Entwicklungskosten E, Einsatz b, Gesamtkosten E + N·b, Faktor und Aufschlag, je Fahrzeug in dessen Zähleinheit.

Zähleinheiten (nie über Fahrzeuge geteilt):
  Rundtour       eine Auswertung ist ein bewerteter Kandidat (`2opt_b5` kostet bis zu 5, jede andere Zugart 1); ℓ = 50·n je Instanz.
  Einplanung     eine Auswertung ist eine Regel auf der Trainingsmenge von 20 Instanzen; ein Einsatz auf einer neuen Instanz ist 1/20 Auswertung.
  Bin Packing    wie Einplanung (20 Trainingsinstanzen); eine Menge der Größe k kostet im Einsatz k Instanzläufe.
Dazu die zweite Einheit der Einplanung, die Knotenauswertungen (Knoten × Regel × Instanzen × Aufträge × (Aufträge + 1) / 2)."""

from fractions import Fraction

import mek_constants as C

TRAININGSINSTANZEN = 20
EINHEIT = {
    "Rundtour": "Auswertungen (bewertete Kandidaten)",
    "Einplanung": "Auswertungen (Regel auf 20 Trainingsinstanzen)",
    "Bin Packing": "Auswertungen (Regel auf 20 Trainingsinstanzen)",
}


def kontrollstufe(n: int) -> int:
    """ℓ = 50·n Auswertungen je Instanz (Rundtour)."""
    return C.LO_F * n


def entwicklung_rundtour(art: str, k: int, n: int) -> int:
    """E der gelernten Mischung = K·ℓ, der gelernten Einzelheuristik = 8·K·ℓ (acht Einzelheuristiken auf K Trainingsinstanzen)."""
    if art not in C.ARTEN:
        raise ValueError(f"unbekannte Art: {art}")
    if k < 0:
        raise ValueError("K darf nicht negativ sein")
    faktor = 1 if art == "mix" else C.K
    return faktor * k * kontrollstufe(n)


def entwicklung_in_stufen(art: str, k: int) -> int:
    """E in Vielfachen von ℓ (Mischung K, Einzelheuristik 8 K): damit rechnet das Break-even."""
    return (1 if art == "mix" else C.K) * k


def gesamt(e: float, n_inst: int, b: float) -> float:
    """C(N) = E + N·b."""
    return e + n_inst * b


def aufschlag(e: float, n_inst: int, b: float) -> float:
    """α(N) = C(N) / (N·b) = 1 + E / (N·b): Gesamtkosten gegen den Einsatz allein."""
    if n_inst <= 0 or b <= 0:
        raise ValueError("N und b müssen positiv sein")
    return (e + n_inst * b) / (n_inst * b)


def faktor(e_meta: float, e_gegner: float) -> float:
    """Wie viele Auswertungen die Meta-Ebene gegenüber dem Gegner vorab braucht (Ganzzahl-Division, Zähleinheit gleich)."""
    if e_gegner <= 0:
        raise ValueError("Der Gegner braucht mindestens eine Auswertung")
    return e_meta / e_gegner


def faktor_bruch(e_meta: int, e_gegner: int) -> Fraction:
    return Fraction(e_meta, e_gegner)


def gleiche_gesamtzahl_budget(e_meta: float, e_gegner: float, n_inst: int, b_meta: float) -> float:
    """β'(N) = b_M + (E_M - e_F) / N: Budget je Instanz, das der Gegner bei gleicher Gesamtzahl ausgeben darf."""
    return b_meta + (e_meta - e_gegner) / n_inst


def knoten_je_auswertung(knoten: int, instanzen: int, n: int) -> int:
    """Knotenauswertungen einer Auswertung (Regel auf `instanzen` Instanzen mit n Aufträgen): Knoten × Instanzen × n (n + 1) / 2."""
    return knoten * instanzen * n * (n + 1) // 2


def auswertungen_bei_gleicher_zeit(auswertungen: int, sekunden_gegner: float, sekunden_meta: float) -> float:
    """Zweite Zähleinheit: Hat die Meta-Ebene je 1 000 Auswertungen `sekunden_meta` und der Gegner `sekunden_gegner`, darf die Meta-Ebene bei gleicher
    Rechenzeit nur auswertungen * sekunden_gegner / sekunden_meta Auswertungen ausgeben (gesetzte Werte im Test, nie ein Befund)."""
    if sekunden_meta <= 0 or sekunden_gegner <= 0:
        raise ValueError("Zeiten müssen positiv sein")
    return auswertungen * sekunden_gegner / sekunden_meta
