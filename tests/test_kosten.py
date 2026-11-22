"""Kostenbuch: Zählregel, Gesamtbilanz, Faktoren (exakt), Aufschlag, Knotenauswertungen, zweite Zähleinheit, Orakelwahl von Hand (Bin Packing)."""

from fractions import Fraction as Fr

import pytest

import mek_constants as C
import mek_kosten as KO


def test_zaehlregel_h1():
    folge = [0, 7, 1, 7, 4, 2]                       # swap, 2opt_b5, insert, 2opt_b5, oropt2, 2opt
    assert sum(C.KOSTEN[h] for h in folge) == 14     # 1 + 5 + 1 + 5 + 1 + 1
    anwendungen_b5 = Fr(2, 6)
    assert Fr(sum(C.KOSTEN[h] for h in folge if h == 7), 14) == Fr(10, 14)
    a = Fr(1, 8)                                     # Gleichverteilung: Anteil von 2opt_b5 an den Anwendungen
    assert 5 * a / (5 * a + 1 - a) == Fr(5, 12) and anwendungen_b5 == Fr(1, 3)


def test_gesamtbilanz_h3():
    lo = KO.kontrollstufe(30)
    assert lo == 1500
    assert [KO.entwicklung_rundtour("mix", k, 30) for k in (1, 3, 10, 30)] == [1500, 4500, 15000, 45000]
    assert [KO.entwicklung_rundtour("einzel", k, 30) for k in (1, 3, 10, 30)] == [12000, 36000, 120000, 360000]
    assert KO.gesamt(15000, 30, 1500) == 60000 and KO.gesamt(0, 30, 1500) == 45000
    assert Fr(60000, 45000) == Fr(4, 3) and abs(KO.aufschlag(15000, 30, 1500) - 4 / 3) < 1e-12
    assert KO.gleiche_gesamtzahl_budget(15000, 0, 30, 1500) == 2000          # β' = 1 500 + 15 000 / 30
    assert KO.entwicklung_in_stufen("mix", 10) == 10 and KO.entwicklung_in_stufen("einzel", 3) == 24


def test_faktoren_h4_exakt():
    assert [round(KO.faktor(b, 11), 1) for b in (1000, 4000, 16000)] == [90.9, 363.6, 1454.5]
    assert [round(KO.faktor(b, 11)) for b in (1000, 4000, 16000)] == [91, 364, 1455]
    assert [round(KO.faktor(b, 161), 1) for b in (1000, 4000, 16000)] == [6.2, 24.8, 99.4]
    assert KO.faktor_bruch(16000, 11) == Fr(16000, 11)
    assert round(KO.faktor(1000, 64), 1) == 15.6 and round(KO.faktor(1000, 21), 1) == 47.6 and 32 * 32 == 1024


def test_knotenauswertungen():
    assert KO.knoten_je_auswertung(14, 20, 10) == 15400 and KO.knoten_je_auswertung(14, 20, 40) == 229600


def test_aufschlag_faellt_streng_mit_n_und_geht_gegen_eins():
    werte = [KO.aufschlag(4500, n, 1500) for n in (1, 2, 5, 10, 100, 1000, 100000)]
    assert all(a > b for a, b in zip(werte, werte[1:])) and werte[-1] < 1.001
    with pytest.raises(ValueError):
        KO.aufschlag(1, 0, 1)
    with pytest.raises(ValueError):
        KO.faktor(5, 0)
    with pytest.raises(ValueError):
        KO.entwicklung_rundtour("xyz", 1, 30)


def test_zweite_zaehleinheit_h6():
    assert round(KO.auswertungen_bei_gleicher_zeit(1000, 1.0, 1.8)) == 556 and int(KO.auswertungen_bei_gleicher_zeit(1000, 1.0, 1.8)) == 555
    with pytest.raises(ValueError):
        KO.auswertungen_bei_gleicher_zeit(1000, 0.0, 1.0)


CAP = 10
INSTANZEN = [[5, 6, 9, 2, 3, 6, 4, 4], [1, 2, 2, 7, 2, 5, 7, 2], [1, 8, 4, 2, 5, 2, 3, 3]]
HAND = {
    (0, "FF"): [[5, 2, 3], [6, 4], [9], [6, 4]], (0, "BF"): [[5, 3], [6, 2], [9], [6, 4], [4]], (0, "WF"): [[5, 2], [6, 3], [9], [6, 4], [4]],
    (1, "FF"): [[1, 2, 2, 2, 2], [7], [5], [7]], (1, "BF"): [[1, 2, 2, 5], [7, 2], [7, 2]], (1, "WF"): [[1, 2, 2, 2], [7], [5, 2], [7]],
    (2, "FF"): [[1, 8], [4, 2, 2], [5, 3], [3]], (2, "BF"): [[1, 8], [4, 2, 2], [5, 3], [3]], (2, "WF"): [[1, 8], [4, 2, 3], [5, 2, 3]],
}


def _packen(gegenstaende, regel):
    rest, inhalt = [], []
    for s in gegenstaende:
        passend = [i for i, r in enumerate(rest) if r >= s]
        if not passend:
            rest.append(CAP - s)
            inhalt.append([s])
            continue
        j = passend[0] if regel == "FF" else (min(passend, key=lambda i: (rest[i] - s, i)) if regel == "BF" else max(passend, key=lambda i: (rest[i], -i)))
        rest[j] -= s
        inhalt[j].append(s)
    return inhalt


def _optimum(gegenstaende):
    """Bitmasken-DP: kleinste Zahl Behälter über alle Teilmengen (anderer Rechenweg als die Regeln)."""
    n = len(gegenstaende)
    summe = [sum(gegenstaende[i] for i in range(n) if m >> i & 1) for m in range(1 << n)]
    dp = [99] * (1 << n)
    dp[0] = 0
    for m in range(1, 1 << n):
        sub = m
        while sub:
            if summe[sub] <= CAP and dp[m ^ sub] + 1 < dp[m]:
                dp[m] = dp[m ^ sub] + 1
            sub = (sub - 1) & m
    return dp[-1]


def test_orakelwahl_von_hand_h5():
    for (i, regel), erwartet in HAND.items():
        assert _packen(INSTANZEN[i], regel) == erwartet
    zahl = {r: [len(HAND[(i, r)]) for i in range(3)] for r in ("FF", "BF", "WF")}
    assert zahl == {"FF": [4, 4, 4], "BF": [5, 3, 4], "WF": [5, 4, 3]} and all(sum(v) == 12 for v in zahl.values())
    orakel = [min(zahl[r][i] for r in zahl) for i in range(3)]
    assert orakel == [4, 3, 3] and sum(orakel) == 10 and Fr(12 - 10, 12) == Fr(1, 6)
    assert [_optimum(x) for x in INSTANZEN] == [4, 3, 3] and [-(-sum(x) // CAP) for x in INSTANZEN] == [4, 3, 3]
    assert 3 * 3 == 9 and sum(max(zahl[r][i] for r in zahl) for i in range(3)) == 13       # 9 Läufe gegen 3; eine Wahl mit einem Lauf: 10 bis 13
