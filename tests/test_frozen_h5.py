"""Eingefrorene Messung H5 (data/mek_h5.json): Schema, Plausibilität und Neu-Rechnen als Band (nicht bitgleich über Plattformen)."""

import sys
from pathlib import Path


import mek_constants as C
import mek_frozen as F

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))


def test_schema_und_meta():
    d = F.h5()
    assert F.schema_fehler_h5(d) == []
    m = d["meta"]
    assert m["wiederholungen"] == 5 and m["instanzen"] == 30 and m["laeufe"] == 5 and m["ks"] == [1, 3, 10, 30] and len(m["zellen"]) == 6
    assert m["auswertungen_gesamt"] > 5e8 and "SplitMix64" in m["zufall"]


def test_kurve_des_gegners_faellt_mit_dem_budget():
    d = F.h5()
    for akz in C.H5_AKZ:
        for zn in d["meta"]["zellen"]:
            k = d["kurve"][akz][zn]
            assert all(b <= a for a, b in zip(k, k[1:])), (akz, zn)               # Mittel über 150 Läufe, alle Stützstellen derselben Läufe: streng nicht steigend
            assert k[0] > k[-1] > 0.0                                            # kein Lauf unter der Referenz im Mittel
            assert abs(sum(x[0] for x in d["kurve_inst"][akz][zn]) / 30 - k[0]) < 1e-3


def test_keine_laufmenge_unter_der_referenz():
    d = F.h5()
    for akz in C.H5_AKZ:
        for zn in d["meta"]["zellen"]:
            assert all(x >= -1e-6 for z in d["kurve_inst"][akz][zn] for x in z)  # Referenz = Minimum über alle Läufe: Abstand nie negativ
            assert all(x > 0 for ws in d["mix"][akz][zn] for z in ws for x in z)


def test_gewichte_sind_verteilungen_mit_untergrenze():
    d = F.h5()
    for akz in C.H5_AKZ:
        for zn in d["meta"]["zellen"]:
            for wdh in d["p"][akz][zn]:
                for p in wdh:
                    assert len(p) == 8 and abs(sum(p) - 1.0) < 1e-5 and min(p) >= C.P_BODEN / (1 + 8 * C.P_BODEN) - 1e-6


def test_gelernte_einzelheuristik_ist_ein_gueltiger_index_und_meist_die_2opt_familie():
    d = F.h5()
    wahl = [h for akz in C.H5_AKZ for zn in d["meta"]["zellen"] for wdh in d["einzel"][akz][zn] for h in wdh]
    assert all(0 <= h < 8 for h in wahl)
    assert sum(h in (2, 3, 7) for h in wahl) >= 0.7 * len(wahl)              # Stück 1: die 2-opt-Zugarten sind die besten Einzelheuristiken


def test_neu_rechnen_als_band():
    """Eine Zelle, 5 Instanzen, Wiederholung 0, K = 3: der Gewinn der gelernten Mischung hat dasselbe Vorzeichen wie in der Datei, und der Gegner bei ℓ liegt im Band
    (die Referenz der Datei ist ein Minimum über mehr Läufe: ihre Abstände sind höchstens 0,6 Punkte größer)."""
    import mek_make_h5 as MK
    g, m, se = MK.rechne_check()
    d = F.h5()
    gespeichert = sum(x[0] for x in d["kurve_inst"]["rr"]["gleich/30"][:5]) / 5
    assert -0.05 <= gespeichert - g <= 0.6
    assert g - m > -3 * se - 0.5                                                         # Mischung nicht deutlich schlechter als der Gegner (Datei: rr, klein: besser)
    stored_gain = F.gewinn("rr", "gleich/30", "mix", 3, "lo")
    assert stored_gain > 0 and abs((g - m) - stored_gain) < max(3 * se, 1.0)


def test_check_werkzeug_laeuft():
    import mek_make_h5 as MK
    assert MK.check() == 0
