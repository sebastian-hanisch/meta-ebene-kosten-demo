"""Konstanten: Namen und Werte der kopierten Rundtour-Module, Raster der Messung, Schwellen der Verdikte, Regler-Grenzen, Farben und Presets.

Die Namen im ersten Block müssen mit denselben Werten in `hhw_constants.py` (Stück 1) und `zgm_constants.py` (Stück 2) stehen, weil die
Kopien (`mek_scenario.py`, `mek_moves.py`, `mek_accept.py`, `mek_search.py`, `mek_select.py`) sie lesen; `tests/test_copies.py` vergleicht sie."""

# ---------------------------------------------------------------- Rundtour: Namen der Kopien (Werte wie in Stück 1 und 2)
HNAMEN = ("swap", "insert", "2opt", "2opt_lokal", "oropt2", "oropt3", "dbridge", "2opt_b5")
K = 8
KOSTEN = (1, 1, 1, 1, 1, 1, 1, 5)
H_2OPT, H_2OPT_B5 = 2, 7
ALLE_ZUGARTEN = tuple(range(K))
B5_STICHPROBEN = 5
LOKAL_LMAX = 8
FAMILIEN = ("gleich", "cluster", "gitter")
FAMILIE_HAND = "hand"
SEITE = 1000.0
CLUSTER_ZAHL, CLUSTER_SIGMA = 5, 40.0
GITTER_FAKTOR, GITTER_RAUSCHEN = 1.5, 0.1
ZWECK_INSTANZ, ZWECK_START, ZWECK_LAUF, ZWECK_BOOT = 11, 33, 24, 7
EPS = 1e-9
RHO = 0.01
LA_LEN, LA_LEN_KURZ = 50, 10
GD_END = 0.80
SA_T0, SA_T1 = 0.3, 0.003
MARKE_KLAR, MARKE_GLEICH = 0.25, 0.10
CF_ALPHA, CF_PHI0, CF_PHI_ERFOLG, CF_PHI_SCHRITT, CF_PHI_MIN, CF_ZEITFENSTER, CF_RAUSCHEN = 0.9, 0.5, 0.99, 0.01, 0.01, 50, 1e-9
LAUT_A, LAUT_BODEN = 0.05, 0.01
Q_EPS, Q_ALPHA, Q_GAMMA = 0.1, 0.1, 0.5
GLEICHE_KONSTANTEN = (
    "HNAMEN", "K", "KOSTEN", "H_2OPT", "H_2OPT_B5", "ALLE_ZUGARTEN", "B5_STICHPROBEN", "LOKAL_LMAX", "FAMILIEN", "FAMILIE_HAND", "SEITE",
    "CLUSTER_ZAHL", "CLUSTER_SIGMA", "GITTER_FAKTOR", "GITTER_RAUSCHEN", "ZWECK_INSTANZ", "ZWECK_START", "ZWECK_LAUF", "ZWECK_BOOT", "EPS",
    "RHO", "LA_LEN", "LA_LEN_KURZ", "GD_END", "SA_T0", "SA_T1", "MARKE_KLAR", "MARKE_GLEICH",
    "CF_ALPHA", "CF_PHI0", "CF_PHI_ERFOLG", "CF_PHI_SCHRITT", "CF_PHI_MIN", "CF_ZEITFENSTER", "CF_RAUSCHEN", "LAUT_A", "LAUT_BODEN",
    "Q_EPS", "Q_ALPHA", "Q_GAMMA",
)

# ---------------------------------------------------------------- Messung H5 (Rundtour, Training der Auswahl)
FAMILIEN_ANZEIGE = {"gleich": "gleichverteilt", "cluster": "Gruppen", "gitter": "Gitter"}
H5_NS = (30, 60)
H5_ZELLEN = tuple((f, n) for f in FAMILIEN for n in H5_NS)          # 6 Zellen
H5_INSTANZEN = 30                                                    # Testinstanzen 0 bis 29 je Zelle
H5_SEEDS = 5                                                         # Läufe (Startlösung und Strom) je Instanz
H5_WDH = 5                                                           # Wiederholungen des Trainings (Vormessung: 3)
H5_KS = (1, 3, 10, 30)
H5_TRAIN_OFFSET = 1000                                               # Trainingsinstanz k der Wiederholung r: 1000 + 30 r + k
H5_TRAIN_SEED_ZWECK = 44                                             # Zufalls-Seed-Zweck des Trainings
H5_MULTS = (1, 1.5, 2, 3, 4, 6, 8, 12, 16, 24, 32)                   # Stützstellen der Budgetkurve in Vielfachen von lo
LO_F, HI_F = 50, 200                                                 # lo = 50 n, hi = 200 n Auswertungen je Instanz
H5_AKZ = ("rr", "la")
AKZ_ANZEIGE = {"rr": "Rekord-zu-Rekord", "la": "Late Acceptance (L = 50)"}
STUFEN = ("lo", "hi")
STUFEN_ANZEIGE = {"lo": "klein (50·n)", "hi": "groß (200·n)"}
ARTEN = ("mix", "einzel")
ARTEN_ANZEIGE = {"mix": "gelernte Mischung", "einzel": "gelernte Einzelheuristik"}
P_BODEN = 0.02                                                       # Untergrenze der Gewichte der gelernten Mischung
MARKE_GEWINN = 0.25                                                  # Prozentpunkte: Marke von Stück 1, gesetzt
N_STERN_GRENZE = 30                                                  # „lohnt“ heißt hier N* höchstens 30 (Vorab-Regel der Vormessung)

# ---------------------------------------------------------------- Einplanung und Bin Packing (Raster des Gegners)
EP_REGIME = ("klein", "gross")
EP_REGIME_ANZEIGE = {"klein": "klein", "gross": "groß"}
EP_FAMILIEN = ("E", "M", "W", "S")
EP_BUDGETS = (500, 1000, 2000, 4000, 8000, 16000)
EP_B = (1000, 4000, 16000)
EP_RASTER = (11, 41, 81, 161)                                        # ATC(k): Zahl der k-Werte = Auswertungen der Einstellung
EP_K_VON, EP_K_BIS = 0.1, 6.0
BP_FAMILIEN = ("gl_20_70", "clu3", "stark")
BP_PR2_GRID = (8, 16, 32)                                            # g x g Gitter: 64, 256, 1 024 Auswertungen
BP_PR2_LAMBDA = (0.0, 1.0)
BP_PR2_M = (0.02, 0.4)
BP_LAEUFE = 20
BP_K = (1, 3, 5)
BP_BUDGETS = (200, 1000)

# ---------------------------------------------------------------- Verdikte (gesetzt, nicht abgeleitet)
V_ERFOLG = 0.5                  # verdict_kosten: success, wenn besser in mindestens der Hälfte der Zellen
V_WARN_ANTEIL = 1 / 8           # warning, wenn besser in höchstens einem Achtel der Zellen ...
V_WARN_FAKTOR = 10              # ... und der Faktor mindestens 10 ist
LOHNT_ANTEIL = 2 / 3            # verdict_breakeven: success ab 2/3 der Zellen, die „lohnen“ ...
LOHNT_WARN = 1 / 6              # ... warning bis 1/6
ERZEUGEN_LUECKE = 20            # verdict_erzeugen: warning, wenn Test um mehr als 20 Prozentpunkte unter dem Training liegt
ZEIT_VERHAELTNIS = 1.25         # verdict_zeit: warning ab diesem Verhältnis größter zu kleinster Wert
KARTE_ERFOLG = 2 / 3
KARTE_WARN = 1 / 6

# ---------------------------------------------------------------- Regler
N_STUFEN = (1, 2, 5, 10, 20, 30, 50, 100, 200, 500, 1000, 2000)
DEFAULT_N = 30
R_STUFEN = ("nie", "1000", "300", "100", "30", "10")
PROBE_K_MAX, PROBE_INSTANZEN, PROBE_SEEDS = 3, 8, 2
PROBE_N = 30
PROBE_MAX_AUSWERTUNGEN = 150_000
ZEIT_AUSWERTUNGEN, ZEIT_WDH, ZEIT_N = 5000, 3, 30
ZEIT_REGELN = ("rand", "cf", "laut", "q", "s2", "s7")
ZEIT_ANZEIGE = {"rand": "Zufallsauswahl", "cf": "Choice Function", "laut": "Lernautomat", "q": "Q-Lernen", "s2": "2opt allein", "s7": "2opt_b5 allein"}
SEED_MAX = 999

# ---------------------------------------------------------------- Farben
COLOR_M = "#2F6B65"
COLOR_F = "#4c78a8"
COLOR_WARN = "#e45756"
COLOR_GRAU = "rgba(150,150,150,0.75)"
COLOR_BAND = "rgba(47,107,101,0.18)"

# ---------------------------------------------------------------- Presets (Schlüssel wie in mek_presets.PRESET_KEYS)
_STD = dict(fahrzeug="Rundtour", n_inst=30, rt_n=30, rt_k=3, rt_art="mix", ep_regime="gross", ep_b=16000, ep_g=11, ep_familie="M",
            bp_familie="gl_20_70", bp_k=3, bp_pr2=64, h5_zelle="alle sechs", h5_akz="rr", h5_stufe="lo", h5_r="nie",
            e3_fahrzeug="Einplanung", karte_fahrzeug="alle", karte_stabil=False, zeit_seed=0)
PRESETS = {
    "Rundtour: Rekord-zu-Rekord, kleines Budget (K = 3)": dict(_STD),
    "Rundtour: Late Acceptance, kleines Budget": dict(_STD, h5_akz="la", rt_n=60),
    "Rundtour: großes Budget (K = 10)": dict(_STD, rt_k=10, h5_stufe="hi"),
    "Rundtour: gelernte Einzelheuristik (K = 3)": dict(_STD, rt_art="einzel", h5_akz="la"),
    "Einplanung: GP gegen ATC(k)": dict(_STD, fahrzeug="Einplanung", e3_fahrzeug="Einplanung", ep_g=161),
    "Bin Packing: Regeln und Mengen": dict(_STD, fahrzeug="Bin Packing", e3_fahrzeug="Bin Packing", bp_pr2=1024),
    "Handbeispiel (gleich/30, K = 1)": dict(_STD, rt_k=1, h5_zelle="gleich/30"),
    "Zeit messen": dict(_STD, karte_fahrzeug="Rundtour", zeit_seed=1),
}
PRESET_HELP = {
    "Rundtour: Rekord-zu-Rekord, kleines Budget (K = 3)": "Rundtour, Training der Auswahl mit 3 Trainingsinstanzen, Einsatz 50·n Auswertungen, Akzeptanz Rekord-zu-Rekord, alle sechs Zellen.",
    "Rundtour: Late Acceptance, kleines Budget": "Dieselbe Frage unter Late Acceptance: dort verliert die gelernte Auswahl schon bei gleichem Einsatz.",
    "Rundtour: großes Budget (K = 10)": "Einsatz 200·n Auswertungen und 10 Trainingsinstanzen: die vorab festgelegte Wahl der Vormessung.",
    "Rundtour: gelernte Einzelheuristik (K = 3)": "Statt einer Mischung wird nur die beste Einzelheuristik gelernt; das Training kostet das Achtfache.",
    "Einplanung: GP gegen ATC(k)": "Erzeugte Prioritätsregeln gegen ATC(k) mit 161 statt 11 k-Werten: Faktor der Auswertungen und Zählung auf frischen Instanzen.",
    "Bin Packing: Regeln und Mengen": "Erzeugte Platzierungsregeln, das feine PR2-Gitter und Mengen mit Orakelwahl gegen Best Fit.",
    "Handbeispiel (gleich/30, K = 1)": "Eine Zelle (gleichverteilt, 30 Orte), 1 Trainingsinstanz: der Weg von der Kurve des Gegners zum Break-even N*.",
    "Zeit messen": "Nur die Zeit-Probe von Frage 5 mit einem anderen Zufalls-Seed; die Rechnung startet mit dem Knopf.",
}
