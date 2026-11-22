# Lohnt die Meta-Ebene? Eine Kostenrechnung in Auswertungen

<!-- Live-Link nach dem Deploy: **[→ Demo live ausprobieren](https://sebastianhanisch-meta-ebene-kosten-demo.streamlit.app/)** -->

Eine **Hyperheuristik** wählt oder erzeugt Heuristiken, statt selbst eine Lösung zu suchen. Das kostet **Auswertungen**, bevor die erste Instanz gelöst ist: Training, Suche im Regelraum, mehrere Läufe je Instanz.
Diese Demo rechnet die Gesamtkosten der Meta-Ebene (Entwicklung plus N Einsätze) gegen eine feste Heuristik, die man hätte nehmen können, und fragt, ab wie vielen Instanzen sich der Aufwand auszahlt und ob überhaupt.
Sie ist der Zusammenfluss der Reihe „Hyperheuristiken erklärt“ (Bereich Optimierung, Feld Metaheuristiken und Suche) und rechnet an drei erzeugten Modellen: Rundtour, Einplanung (eine Maschine, gewichtete Verspätung) und Bin Packing (online).
Verweise auf andere Demos der Reihe nennen nur ihren Namen (Hyperheuristik, Zugmenge, Auswahlregeln, Akzeptanz mal Auswahl, Prioritätsregel-Evolution, Platzierungsfunktion, Regel-Verteilungswechsel, Heuristik-Variation).

## Kernfrage

**Die Meta-Ebene kostet Auswertungen, bevor die erste Instanz gelöst ist. In diesen Messungen (drei erzeugte Modelle, eigene Umsetzungen, kleine Budgets, Zähleinheit Auswertungen je Fahrzeug) zahlte sie sich nur unter bestimmten Bedingungen aus:
das Training der Auswahl auf der Rundtour zahlte sich bei N = 30 am ehesten unter Rekord-zu-Rekord mit kleinem Budget und kleinem K aus (K = 1: 5 von 6 Zellen); unter Rekord-zu-Rekord mit großem Budget lohnte es sich in 4 / 3 / 3 / 1 von 6 Zellen (K = 1 / 3 / 10 / 30), unter Late Acceptance mit kleinem Budget in keiner Zelle, mit großem Budget in höchstens 2 von 6; die Erzeugung von Regeln (GP) ist gegen ATC(k) mit 11 Werten bei 16 000 Auswertungen in 2 von 8 Zellen besser (alle im Regime groß), in 3 schlechter, wobei GP das 1 455-Fache der Auswertungen von ATC mit 11 Werten braucht (das 99,4-Fache bei 161 Werten); gierig zusammengestellte Mengen der Größe k = 3 (Bin Packing, drei Pools, drei Familien) gewannen gegen Best Fit nur mit Orakelwahl (3 Läufe je Instanz), nicht mit der Merkmalswahl (1 Lauf).
Das ist ein Befund für diese Messbereiche und diese Umsetzungen, keine Aussage über Hyperheuristiken im Allgemeinen und keine über irace, HyFlex oder Sprachmodelle.**

Das Rückgrat der Reihe: In den Messungen der Reihe hing es auf der Rundtour an der Akzeptanzregel und (nach dem Stück zur Zugmenge, mit einer nachträglich gewählten Teilmenge) an der Zugmenge ab, ob Lernen hilft; bei Einplanung und Bin Packing sind feste Gegner (ATC(k) mit eingestelltem k, Best Fit ohne Einstellung) stark, und die Meta-Ebene kostet ein Vielfaches an Auswertungen.

Hook als Befund (Rundtour, 6 Zellen, 30 Testinstanzen × 5 Läufe, 5 Wiederholungen des Trainings, Einsatz 50·n Auswertungen je Instanz, Mischung): unter Rekord-zu-Rekord lohnt sich das Training der Auswahl bei N = 30 Instanzen in allen Wiederholungen für K = 1: 5 von 6 (Mittel 6), K = 3: 4 von 6 (Mittel 6), K = 10: 1 von 6 (Mittel 3), K = 30: 0 von 6 (Mittel 0); unter Late Acceptance lohnt es sich mit diesem Budget bei N = 30 in keiner Zelle (K = 1: 0 von 6 (Mittel 0), K = 3: 0 von 6 (Mittel 0), K = 10: 0 von 6 (Mittel 0), K = 30: 0 von 6 (Mittel 0); kleinstes N* im Mittel der Wiederholungen 32,4 Instanzen bei K = 1 in gleich/60), mit großem Budget (200·n) in höchstens 2 von 6 Zellen.
Das K der Antwort ist selbst ein Teil des Befunds.

## Befunde und Korrekturen gegenüber der Vormessung

Die Vormessung der Planung rechnete mit `numpy.default_rng`, 3 Wiederholungen des Trainings und dem Mittel der Wiederholungen für N*; diese Demo rechnet mit SplitMix64, 5 Wiederholungen und je Wiederholung ein eigenes N*. Was sich verschoben hat:

* **Training der Auswahl, Rekord-zu-Rekord, klein (50·n):** Der Gewinn bei gleichem Einsatz liegt bei +0,91 (K = 1), +0,93 (K = 3), +1,01 (K = 10) und +0,91 Prozentpunkten (K = 30), die Vormessung nannte +0,72 bis +0,83. K = 10, die vorab festgelegte Wahl, lohnt sich nach dem Mittel der Wiederholungen in 3 von 6 Zellen (Vormessung 0 von 6), in allen Wiederholungen in 1; die Regel „N* ≤ 30 in mindestens 4 von 6 Zellen“ ist damit auch jetzt nicht erfüllt.
* **Groß (200·n):** Der Gewinn bei gleichem Einsatz liegt unter Rekord-zu-Rekord für K = 1 bis 30 zwischen +0,18 und +0,26 Prozentpunkten (Vormessung höchstens +0,15), also um die Marke von 0,25 herum.
* **Late Acceptance, klein:** Das Training lohnt sich in 0 von 6 Zellen für jedes K (wie in der Vormessung); der Gewinn bei gleichem Einsatz ist für K = 1 bis 30 negativ (−0,21 bis −0,09 Prozentpunkte).
* **Gelernte Einzelheuristik, Late Acceptance, K = 3, klein:** lohnt sich in 0 von 6 Zellen (kleinstes N* 72,4; Vormessung: kleinstes N* 80,8).
* **GP gegen ATC(k), 16 000 Auswertungen, 8 Zellen (besser / gleich / schlechter, Regel D1):** 2 / 3 / 3 gegen ATC mit 11 Werten (Vormessung 1 / 4 / 3), 2 / 5 / 1 gegen ATC mit 161 Werten (Vormessung 1 / 4 / 3; für 81 Werte 1 / 3 / 4). Ein feineres Raster macht den Gegner nicht verlässlich besser: der Median seines Regrets ändert sich um −1,59 bis +0,39 Prozentpunkte (negativ = besser; besser in 4, schlechter in 4 von 8 Zellen).
* **Bin Packing:** Die erzeugten Regeln (7 Suchverfahren) sind gegen Best Fit in 0 von 21 Zellen besser, in 6 schlechter (200 und 1 000 Auswertungen; die Vormessung zählte 0 von 27). PR2 mit 256 und 1 024 statt 64 Auswertungen: Median Δ auf frischen Instanzen −0,001 / +0,000 / +0,153 und +0,017 / +0,000 / +0,200 (64: +0,000 / +0,000 / +0,092) Prozentpunkte, alle 9 Zellen nach der Regel „gleich“. In der breit gestreuten Familie liegt PR2 mit größerem Gitter zunehmend über Best Fit (Median +0,1999 bei 1 024 Auswertungen, in 20 von 20 Läufen schlechter); die Regel zählt „gleich“, weil der Median knapp unter der Schwelle 0,2 liegt. Auf dem Training wird PR2 besser (64 Auswertungen −0,195 / −0,209 / −0,204, 1 024 Auswertungen −0,546 / −0,233 / −0,402).
* **Faktoren:** 90,9, 364 und 1 455 (1 000, 4 000, 16 000 Auswertungen gegen 11), gegen 161 Werte 6,2, 24,8 und 99,4 (der Zuschnitt rundete „90 bis 1 450“).
* **Übernommen aus den Demos der Reihe (Stand der Texte nach deren Aussagenprüfung):** Familienwechsel der Einplanung bei 16 000 Auswertungen 54 von 72 Zellen schlechter, 18 gleich, 0 besser (Vormessung 61 von 72); Packen, Familienwechsel (fünf Suchverfahren über Bäume und Schablonen, 1 000 Auswertungen): 13 von 30 Zellen schlechter als Best Fit, 17 gleich, 0 besser; unter Rekord-zu-Rekord bei 50·n gewinnen Choice Function, Lernautomat und Q-Lernen gegen die Zufallsauswahl (+1,14 / +0,84 / +0,88 Prozentpunkte im Mittel über 6 Zellen, Zählung nach Zellenmitteln gegen die Marke 0,25), unter Late Acceptance verlieren sie; die gierig zusammengestellte Menge mit Orakelwahl gewinnt auch aus dem Pool der Zufallssuche.
* **Klassenmarken:** Stück 1 ist die Quelle (0,25 und 0,10 Prozentpunkte); die Demos zur Zugmenge und zu den Auswahlregeln zählen etwas anders. Diese Demo zählt Zellenmittel gegen die Marke 0,25 ohne Intervall.

## Modell

Gesamtkosten der Meta-Ebene C_M(N) = E_M + N·b_M, des festen Gegners C_F(N) = e_F + N·b_F. Bei gleicher Gesamtzahl darf der Gegner je Instanz β′(N) = b_M + (E_M − e_F)/N ausgeben; der **Break-even** N* ist die kleinste Zahl Instanzen, bei der die Meta-Ebene mit ihrem Abstand nicht schlechter ist als der Gegner mit β′(N). Ist Q_M(b_M) ≥ Q_F(b_M), gibt es kein N* („nie“). Die Gütekurve des Gegners ist zwischen den Stützstellen (1, 1,5, 2, 3, 4, 6, 8, 12, 16, 24, 32 mal ℓ = 50·n) linear in ln β. Alle Formeln und die Symboltabelle stehen im Expander „📐 Mathematische Formulierung“ der App.
Die Einheit der Auswertung ist je Fahrzeug eine andere; es gibt keinen Faktor über Fahrzeuge.

## Methodik

* **Rundtour** (n = 30 und 60, Familien gleichverteilt, Gruppen, Gitter; 8 Zugarten; Zufall SplitMix64): 6 Zellen, je 30 Testinstanzen × 5 Läufe, zwei Akzeptanzregeln (Rekord-zu-Rekord, Late Acceptance mit L = 50). Training: gelernte Mischung (ein Lauf der Zufallsauswahl je Trainingsinstanz, Gewicht = mittlere Belohnung je Anwendung, Untergrenze 0,02) und gelernte Einzelheuristik (alle acht einzeln), K = 1, 3, 10, 30 Trainingsinstanzen, 5 Wiederholungen. Gegner: Zufallsauswahl über alle acht Zugarten mit einer Budgetkurve bis 32·ℓ. Referenz je Instanz: Minimum aus den Langläufen der Zugmenge-Demo und allen Läufen dieser Messung (nicht als optimal bewiesen).
* **Einplanung** (1‖ΣwⱼTⱼ, Training mit n = 10 bzw. 40, 20 Trainingsinstanzen, 4 Familien, 20 Läufe je Zelle): die Läufe von GP, (1+1) und Zufallssuche stammen aus der Demo zu den Prioritätsregeln; neu gerechnet ist der Gegner ATC(k) mit k aus 11, 41, 81 und 161 Werten (11 Werte: das Raster der Quelle, ungefähr geometrisch von 0,1 bis 6,0, es reproduziert deren Läufe; 41, 81 und 161 Werte: geometrisch von 0,1 bis 6,0).
* **Bin Packing** (n = 60, Kapazität 100, 3 Familien, 20 Trainingsinstanzen, Test 200 Instanzen, 20 Läufe): die Läufe der Suchverfahren aus der Demo zu den Platzierungsfunktionen, die Mengen aus der Demo zur Heuristik-Variation; neu gerechnet ist PR2 auf Gittern von 8 × 8, 16 × 16 und 32 × 32 (reproduziert für 8 × 8 die Quelle).
* **Zähleinheit** (Frage 1): Rundtour ein bewerteter Kandidat; Einplanung und Bin Packing eine Regel auf der Trainingsmenge von 20 Instanzen, ein Einsatz je Instanz ist 1/20 Auswertung. Zeiten sind nie ein Befund.
* **Vorgerechnet und eingefroren:** `data/mek_h5.json` (Rundtour, rund 620 Millionen Auswertungen nach den Budgets gerechnet, nicht gezählt; `tools/mek_make_h5.py`), `data/mek_gegner.json` (`tools/mek_make_gegner.py`), `data/mek_karte.json` und `data/mek_kosten.json` (`tools/mek_make_karte.py`). Live rechnet die App nur die Probe von Frage 2 und die Zeitmessung von Frage 5.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen mit Voraussetzung im selben Satz; die Spalte „Test“ nennt die Prüfung (`tests/test_claims.py`, Band oder exakt).

| Frage | Befund | Test |
|---|---|---|
| Kosten (Faktor) | GP braucht 90,9-, 364- und 1 455-mal so viele Auswertungen wie ATC(k) mit 11 Werten (1 000, 4 000, 16 000 gegen 11 Auswertungen), 6,2-, 24,8- und 99,4-mal gegen 161 Werte | `test_faktoren`, exakt |
| Break-even, Rundtour | Rekord-zu-Rekord, 50·n, Mischung, N = 30, 6 Zellen, 5 Wiederholungen: K = 1: 5 von 6 (Mittel 6), K = 3: 4 von 6 (Mittel 6), K = 10: 1 von 6 (Mittel 3), K = 30: 0 von 6 (Mittel 0) (in allen Wiederholungen; in Klammern das Mittel der Wiederholungen) | `test_lohnt_zaehlung`, exakt auf der Datei, Neurechnung als Band |
| Break-even, Late Acceptance | Late Acceptance, 50·n, Mischung, N = 30: K = 1: 0 von 6 (Mittel 0), K = 3: 0 von 6 (Mittel 0), K = 10: 0 von 6 (Mittel 0), K = 30: 0 von 6 (Mittel 0) | `test_lohnt_zaehlung` |
| Break-even, groß | Rekord-zu-Rekord, 200·n, Mischung, N = 30: K = 1: 4 von 6 (Mittel 4), K = 3: 3 von 6 (Mittel 4), K = 10: 3 von 6 (Mittel 3), K = 30: 1 von 6 (Mittel 2); Late Acceptance, 200·n: K = 1: 1 von 6 (Mittel 2), K = 3: 2 von 6 (Mittel 3), K = 10: 1 von 6 (Mittel 3), K = 30: 0 von 6 (Mittel 0) | `test_lohnt_zaehlung` |
| Gelernte Einzelheuristik | K = 3, N = 30, 50·n: Rekord-zu-Rekord 0 von 6, Late Acceptance 0 von 6 | `test_lohnt_zaehlung` |
| Gewinn bei gleichem Einsatz | Rekord-zu-Rekord, 50·n, Mittel über 6 Zellen und 5 Wiederholungen: +0,91 / +0,93 / +1,01 / +0,91 Prozentpunkte für K = 1 / 3 / 10 / 30; bei 200·n +0,21 / +0,18 / +0,24 / +0,26 | `test_gewinn`, Band |
| GP gegen ATC(k) | 8 Zellen, 20 Läufe, Regel D1, 16 000 Auswertungen: 2 / 3 / 3 (11 Werte), 2 / 4 / 2 (41), 2 / 5 / 1 (81), 2 / 5 / 1 (161); 4 000 Auswertungen: 1 / 3 / 4 (11), 1 000: 0 / 2 / 6 (11) | `test_gp_gegen_atc`, exakt auf der Datei, mit scipy nachgerechnet |
| GP gegen feste Regeln | beste von SPT, EDD, WSPT, MDD je Zelle, 8 Zellen: 16 000 Auswertungen 8 besser, 4 000 7 besser, 1 000 3 besser (nicht gegen ATC(k)) | `test_gp_gegen_atc` |
| Training gegen Test | GP, 16 000 Auswertungen, Anteil der Läufe unter ATC(k) mit 11 Werten: Training 84 % (klein) und 89 % (groß), frische Instanzen 29 % und 79 % | `test_gp_gegen_atc` |
| Raster des Gegners | 161 statt 11 k-Werte: Median des Regrets von ATC(k) ändert sich um −1,59 bis +0,39 Prozentpunkte (8 Zellen, 20 Läufe) | `test_gp_gegen_atc` |
| Bin Packing, Suche | 7 Suchverfahren × 3 Familien, 20 Läufe, Regel der Platzierungsfunktionen: bei 200 und bei 1 000 Auswertungen 0 besser, 15 gleich, 6 schlechter von 21 Zellen | `test_bin_packing`, exakt auf der Datei |
| Bin Packing, PR2 | Median Δ gegen Best Fit auf frischen Instanzen (gleichverteilt / Häufungen / breit gestreut): +0,000 / +0,000 / +0,092 (64 Auswertungen), −0,001 / +0,000 / +0,153 (256), +0,017 / +0,000 / +0,200 (1 024); alle 9 Zellen nach der Regel „gleich“. In der breit gestreuten Familie liegt PR2 mit größerem Gitter zunehmend über Best Fit (Median +0,1999 bei 1 024 Auswertungen, in 20 von 20 Läufen schlechter); die Regel zählt „gleich“, weil der Median knapp unter der Schwelle 0,2 liegt. | `test_bin_packing` |
| Bin Packing, Training | EA-S, 1 000 Auswertungen, Median Δ Training / Test: −0,722 / −0,244 / −0,568 / +0,064 / +0,033 / +0,243 Prozentpunkte | `test_bin_packing` |
| Mengen | gierige Menge k = 3 gegen Best Fit, mit Orakelwahl (3 Läufe je Instanz): besser in 3 von 3 Familien für jeden der Pools Zufallssuche, EA-S, GP-T; mit Merkmalswahl (1 Lauf) schlechter in 3 von 3 | `test_karte_zeilen` |
| Verteilungswechsel | Familienwechsel, 16 000 Auswertungen: 0 besser, 18 gleich, 54 schlechter von 72 Zellen (Zählung aus der Demo zum Verteilungswechsel) | `test_karte_zeilen` |
| Verteilungswechsel, Packen | Familienwechsel, fünf Suchverfahren über Bäume und Schablonen, 1 000 Auswertungen: 0 besser, 17 gleich, 13 schlechter von 30 Zellen gegen Best Fit (Zählung aus der Demo zum Verteilungswechsel) | `test_verteilungswechsel_packen`, nur mit dem Nachbarordner |
| Online gelernt | unter Rekord-zu-Rekord, 50·n, Mittel über 6 Zellen: Choice Function +1,14, Lernautomat +0,84, Q-Lernen +0,88 Prozentpunkte; unter Late Acceptance −1,57 / −1,18 / −1,36 | `test_karte_zeilen` |
| Teilmenge T3 | gegen die volle Menge, nachträglich gewählt, Zellenmittel (besser / gleich / schlechter von 6): Rekord-zu-Rekord klein 5 / 1 / 0, nur besser klein 4 / 2 / 0, Late Acceptance klein 1 / 1 / 4 | `test_karte_zeilen` |
| Karte | 85 Zeilen, davon 7 „nicht gemessen“ | `test_karte_zeilen` |
| Zeit | keine Zahl: die Zeitmessung ist eine Probe auf dem Rechner des Besuchers; getestet wird nur, dass alle Zeilen gleich viele Auswertungen haben | `test_app_demo` |

Messungen dieser README ohne Test: die Spannen der Wiederholungen je Zelle (stehen in der App-Tabelle), die Gewichte der gelernten Mischungen (`data/mek_h5.json`, nur auf Plausibilität geprüft).

## Ehrliche Grenzen

* **Kleine Maßstäbe, eigene Umsetzungen:** Rundtour n = 30 und 60 mit 8 selbst gewählten Zugarten und Budgets von 50·n und 200·n Auswertungen; Einplanung n = 10 und 40 mit einer Zielfunktion und vier Familien; Bin Packing n = 60 mit einer Kapazität und drei Familien. Gemessen ist weder irace noch HyFlex noch ein echtes Sprachmodell. Die Aussagen gelten nicht für große Budgets, andere Zielfunktionen oder andere Aufgaben.
* **N\* gilt für Instanzen aus derselben Verteilung wie das Training.** Beim Verteilungswechsel ist die Auszahlung nicht mehr gesichert: In der Demo zum Verteilungswechsel war die erzeugte Einplanungsregel (GP, 16 000 Auswertungen) nach einem Familienwechsel in keiner der 72 Zellen besser als ATC(k) (Zeile der Karte in Frage 4). Die Lebensdauer R in Frage 2 rechnet den Wechsel als Obergrenze der Zahl nutzbarer Instanzen.
* **Die Meta-Ebene ist nirgends abgestimmt:** Lernraten, Populationsgrößen und Gewichtsuntergrenzen sind feste, nicht abgestimmte Setzungen. Das kann die Meta-Ebene benachteiligen; die Gegner haben null bis zwei Parameter (Zufallsauswahl und Best Fit keinen, ATC(k) einen, PR2 zwei), und ihre Einstellung kostet Auswertungen.
* **Die Teilmenge T3 wurde nachträglich gewählt,** nach Ansicht der Ergebnisse; ihre Kosten null verschweigen die Kosten der Erkenntnis.
* **Bei kleinem Gewinn ist N\* unsicher:** Es streut über die 5 Wiederholungen schon in einer Zelle um mehr als das Dreifache (Rekord-zu-Rekord, 50·n, gleich/30, K = 3: 15,3 bis 52,9; K = 1: 4,6 bis 74,2, mehr als das 16-Fache); das Runden von Q_M auf zwei Stellen verschiebt N\* in diesen Daten höchstens um das 1,17-Fache. Die Demo zeigt deshalb die Spanne über die Wiederholungen. N\* ist nur definiert, wo der Gegner mit mehr Auswertungen verlässlich besser wird: auf der Rundtour ja (die Kurve der Zufallsauswahl fällt in allen sechs Zellen mit dem Budget); bei Einplanung und Bin Packing sind nur wenige Rasterpunkte des Gegners gemessen, sein Verlauf ist dort nicht durchgehend fallend, und die Demo bietet dort kein Break-even an.
* **Zähleinheit:** Auswertungen sind je Fahrzeug anders definiert, es gibt keinen Faktor über Fahrzeuge. Gleiche Auswertungszahl ist nicht gleiche Rechenzeit (Branke u. a. 2016); Zeiten sind hier nie ein Befund.
* **Nicht gemessen:** eine Menge ohne dominante Zugart, Budgets über 1 000 Auswertungen bei Bin Packing als Zählung, Late Acceptance mit anderer Listenlänge für N\*, die Zustandsabhängigkeit der Auswahl, die Abstimmung der Meta-Ebene und der Nutzen im Betrieb. Die Aussagen sind keine Nutzenbehauptung für Logistik, Lager oder Fertigung: die drei Modelle sind erzeugt.

## Befunde und Korrekturen gegenüber dem Plan

* **Gegner mit Budgetkurve (Einplanung, Bin Packing):** Der Plan erwartete, dass mehr Auswertungen den Gegner nicht verbessern (GP gegen ATC(g) 1 / 4 / 3 bei 11, 41 und 161 Werten, 1 / 3 / 4 bei 81). Gemessen ist: GP steht gegen feinere Raster besser da (2 / 5 / 1 bei 161 Werten), und der Median des Regrets von ATC ändert sich je Zelle um −1,59 bis +0,39 Prozentpunkte. Die Demo sagt deshalb „nicht verlässlich besser“ und bietet für diese Fahrzeuge kein Break-even an.
* **Zahlen der Vormessung** wurden im Bau neu gemessen (siehe oben); die Zahlen der Demos der Reihe stammen aus deren eingefrorenen Dateien.
* **Experimente:** Alle fünf Fragen sind gebaut (Kostenbuch, Break-even mit Probe, Kosten-Nutzen der Erzeugung, Karte, Zeit). Der Plan sah ein Kostenbuch mit einer Zeile je COVERT, ATC2 und Impfung nicht vor; sie fehlen.
* **Karte:** Die Zeilen werden aus den Dateien gezählt; die Online-Zeilen (Choice Function, Lernautomat, Q-Lernen) und die Teilmengen-Zeilen zählen Zellenmittel gegen die Marke 0,25 Prozentpunkte (der Plan nannte die Zählung der Vormessung mit gd und sa; für sie liegen in den Demos der Reihe keine Zellenwerte vor).
* **Kopien:** Rundtour-Kern aus Stück 1 und 2 (`mek_scenario.py`, `mek_moves.py`, `mek_accept.py`, `mek_search.py`, `mek_rngblock.py`, `mek_select.py`, `mek_refs.json`) bytegleich bis auf das Präfix, `mek_rng.py` die Vorlage der Website; die Kopier-Tests überspringen sich ohne Nachbarordner. Der Kern von Einplanung und Bin Packing wird nicht kopiert: `tools/mek_make_gegner.py` liest ihn aus den Nachbardemos, der Neurechnen-Test dafür braucht sie.

## Tests

161 Tests. Zusammensetzung: Handwerte (Break-even, Kosten, Orakelwahl von Hand), Orakel (N* auf drei Wegen, unabhängiger Zähler der Auswertungen, Bilanz, Karte gegen die Quellen), Eigenschaften, Verdikte an gesetzten Werten, Kopier-Tests, Neurechnen als Band, Claims der README (`tests/test_claims.py`), Presets und Layout, App (jedes Preset, Probe, Zeit), Footer, Laufzeit-Importe. Die Neu-Rechnen-Tests sind Bänder, keine bitgleichen Vergleiche (C-Bibliothek und Summenreihenfolge unterscheiden sich zwischen Plattformen).

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Seite: Kopf, fünf Fragen mit Verdikten, Expander, Grenzen, Formeln, Footer |
| `mek_constants.py`, `mek_presets.py`, `mek_layout.py` | Grenzen, Raster, Schwellen, Presets; Permalink und Hervorhebung; fester Kopf |
| `mek_breakeven.py`, `mek_kosten.py` | Break-even N* (Umkehrung der Gegnerkurve), Kostenbuch (E, b, Gesamtkosten, Faktor, Aufschlag) |
| `mek_frozen.py`, `mek_stats.py` | Lader und Zählungen auf den eingefrorenen Dateien, Wilcoxon exakt, beide Entscheidungsregeln |
| `mek_evaluation.py`, `mek_visualization.py`, `mek_texts.py` | Verdikte (reine Funktionen), Kostenbuch-Zeilen, Probe, Zeitmessung; Abbildungen; feste Texte |
| `mek_train.py` | Training der Auswahl (Mischung, Einzelheuristik) auf der Rundtour |
| `mek_rng.py`, `mek_rngblock.py`, `mek_scenario.py`, `mek_moves.py`, `mek_accept.py`, `mek_search.py`, `mek_select.py`, `mek_refs.json` | Kopien aus den Demos zur Hyperheuristik und Zugmenge |
| `data/mek_h5.json`, `data/mek_gegner.json`, `data/mek_karte.json`, `data/mek_kosten.json` | eingefrorene Messungen |
| `tools/mek_make_h5.py`, `tools/mek_make_gegner.py`, `tools/mek_make_karte.py`, `tools/mek_kopien.py`, `tools/mek_readme.py` | erzeugen die Dateien und diese README |
| `tests/` | Testdateien |

## Bewusst nicht umgesetzt

* Landschaftsmerkmale und Auswahl je Instanz (eine andere Frage als „lohnt die Meta-Ebene“).
* Racing und Parameterräume der Einstellung (hier zählt nur die Einstellung des festen Gegners als Kostenzeile).
* Die Zählweise der Nachbarschaft (die zweite Zähleinheit ist die Rechenzeit der Meta-Ebene).
* Eine Messung mit einem Sprachmodell.
* Eine Elementarschritt-Umrechnung zwischen den Fahrzeugen (nicht gemessen).
* Die Abstimmung der Meta-Ebene selbst (Lernraten, Populationsgrößen).
* Eine Menge ohne dominante Zugart, Budgets über 1 000 Auswertungen bei Bin Packing, die Zustandsabhängigkeit der Auswahl (Reserve R).
* Der Nutzen im Betrieb; ein PDF-Export.
* COVERT und ATC2 als Gegner (kein Bestandteil der Läufe der Quelle).

## Lokal ausführen

```
pip install -r requirements.txt
streamlit run app.py
```

Gebaut mit Streamlit, Plotly und NumPy.

Quellen (Belegstufen aus der Literaturrecherche der Reihe): Branke u. a. 2016 (V), Burke u. a. 2013 (V), Sobotka u. a. (V, Vorabdruck arXiv 2509.02782), Sim u. a. (V, arXiv 2501.11411), Herrmann und Pallez (V, arXiv 2510.27353), Rice 1976 (A).

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Hyperheuristiken: Auswählen und Erzeugen](https://sebastianhanisch.net/konzepte-hyperheuristiken.html).
