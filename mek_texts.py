"""Feste Texte der App: Einleitung, einfache Worte, Kernfragen, Erklärtabelle, Grenzen (derselbe Text steht in der README) und der Formelblock.

Zahlen mit Messbezug stehen nicht hier, sondern kommen aus den Verdikt-Funktionen (mek_evaluation) und den eingefrorenen Dateien."""

TITEL = "🧾 Lohnt die Meta-Ebene?"
UNTERTITEL = "Eine Kostenrechnung in Auswertungen"

EINLEITUNG = """
Eine **Hyperheuristik** wählt oder erzeugt Heuristiken, statt selbst eine Lösung zu suchen. Das kostet **Auswertungen**, bevor die erste Instanz gelöst ist: Training, Suche im Regelraum, mehrere Läufe je Instanz. Diese Demo rechnet die **Gesamtkosten der Meta-Ebene** gegen eine feste Heuristik, die man hätte nehmen können, und fragt, ab wie vielen Instanzen sich der Aufwand auszahlt und ob überhaupt. Gemessen ist das an drei erzeugten Modellen (Rundtour, Einplanung, Bin Packing) mit eigenen Umsetzungen und kleinen Budgets; die Ergebnisse gelten nur dort.

Zusammenfluss der Reihe „Hyperheuristiken erklärt“: In den Messungen der Reihe hing es auf der Rundtour an der Akzeptanzregel und (nach dem Stück zur Zugmenge, mit einer nachträglich gewählten Teilmenge) an der Zugmenge ab, ob Lernen hilft (Stücke zur Hyperheuristik, zur Zugmenge, zu den Auswahlregeln und zu Akzeptanz mal Auswahl). Bei Einplanung und Bin Packing sind feste Gegner (ATC(k) mit eingestelltem k, Best Fit ohne Einstellung) stark, und die Meta-Ebene kostet ein Vielfaches an Auswertungen. Unten stehen `🚧 Wo die Annahmen enden` und `📐 Mathematische Formulierung`.
"""

IN_EINFACHEN_WORTEN = """
Stellen Sie sich vor, Sie nehmen für jede Aufgabe einfach ein bewährtes Verfahren. Oder Sie bauen vorher eine Auswahl, die lernt, wann welches Verfahren passt. Das Lernen kostet Rechenschritte, bevor die erste echte Aufgabe gelöst ist. Es lohnt sich erst, wenn viele Aufgaben folgen und die Auswahl dann besser ist als das bewährte Verfahren, dem man dieselbe Gesamtzahl an Schritten gegeben hätte. In den Messungen war der Gewinn klein, und eine Menge von Verfahren, die man erst nach Ansicht der Ergebnisse auswählte, erreichte ihn ohne Lernen. Bei Einplanung und Bin Packing brachten mehr Schritte für den festen Gegner in den gemessenen Rastern nicht verlässlich etwas. Die Demo zählt die Schritte, zeigt, ab wann sich Lernen auszahlt, wo es sich nie auszahlt und warum gleiche Schrittzahl nicht gleiche Rechenzeit heißt.
"""

KERNFRAGEN = {
    1: "Was kostet die Meta-Ebene vorab?",
    2: "Ab wie vielen Instanzen zahlt sich das Training aus?",
    3: "Bringt mehr Aufwand beim Erzeugen mehr auf frischen Instanzen?",
    4: "Wo lohnt es, wo nicht?",
    5: "Gleiche Auswertungszahl, gleiche Arbeit?",
}

ZAEHLEINHEIT_HINWEIS = (
    "Zähleinheit: Auf der Rundtour ist eine Auswertung ein bewerteter Kandidat (die Zugart `2opt_b5` kostet bis zu 5, jede andere 1). Bei Einplanung und Bin Packing ist eine Auswertung "
    "eine Regel, die auf der Trainingsmenge von 20 Instanzen ausgewertet wird; ein Einsatz auf einer neuen Instanz ist ein Instanzlauf, also 1/20 Auswertung, und eine Menge der Größe k "
    "kostet im Einsatz k Instanzläufe. Die drei Einheiten haben nichts miteinander zu tun: Die Demo bildet nie einen Faktor zwischen zwei Fahrzeugen."
)

KLASSEN_HINWEIS = (
    "Die Klassenmarken (0,25 und 0,10 Prozentpunkte) stammen aus der Demo zur Hyperheuristik (Stück 1); die Demos zur Zugmenge und zu den Auswahlregeln zählen etwas anders. "
    "Die Karte zählt deshalb Zellenmittel gegen die Marke 0,25 Prozentpunkte ohne Intervall und nennt die Regel in jeder Zeile."
)

ERKLAERTABELLE_MD = """
| Name | Was es ist |
|---|---|
| **Choice Function** | Auswahlregel, die jeder Zugart eine gleitende Wertung aus ihrer bisherigen Leistung, der Leistung nach der letzten Zugart und der Wartezeit gibt |
| **Lernautomat** | Auswahlregel, die die Wahrscheinlichkeit einer Zugart nach einem Erfolg erhöht (linear, nur bei Erfolg) |
| **Q-Lernen** | Auswahlregel mit einem Q-Wert je Zugart und gelegentlicher gleichverteilter Erkundung |
| **gelernte Mischung** | feste Gewichte je Zugart, aus einem Trainingslauf der Zufallsauswahl als mittlere Belohnung je Anwendung gewonnen; kostet K Läufe |
| **gelernte Einzelheuristik** | die Zugart mit dem besten mittleren Ergebnis, nachdem alle acht einzeln auf K Trainingsinstanzen liefen; kostet 8·K Läufe |
| **Rekord-zu-Rekord** | Akzeptanzregel: ein Zug bleibt, wenn er nicht verlängert oder die neue Länge höchstens das 1,01-Fache des Bestwerts ist |
| **Late Acceptance** | Akzeptanzregel: ein Zug bleibt, wenn er nicht verlängert oder die neue Länge höchstens der Eintrag von vor L Schritten ist (hier L = 50) |
| **ATC(k)** | Prioritätsregel der Einplanung (Apparent Tardiness Cost) mit einem Parameter k; hier wird k aus einem Raster auf 20 Trainingsinstanzen gewählt, das kostet so viele Auswertungen wie das Raster Werte hat |
| **GP** | Genetische Programmierung: erzeugt Regelbäume aus Kennzahlen und Rechenoperationen durch Kreuzung und Mutation |
| **PR2** | Zwei-Parameter-Platzierungsregel für Bin Packing (Lückenstrafe λ und Schwelle m), auf einem Gitter gewählt |
| **Orakelwahl** | alle k Regeln einer Menge laufen auf jeder Instanz, die beste Packung zählt: k Läufe je Instanz |
| **Break-even N\\*** | kleinste Zahl künftiger Instanzen, bei der Training plus Einsatz nicht mehr Auswertungen braucht als der Gegner mit derselben Gesamtzahl und dabei nicht schlechter ist |
"""

ASSUMPTIONS_MARKDOWN = """
* **Kleine Maßstäbe, eigene Umsetzungen:** Rundtour n = 30 und 60 mit 8 selbst gewählten Zugarten und Budgets von 50·n und 200·n Auswertungen; Einplanung n = 10 und 40 mit einer Zielfunktion und vier Familien; Bin Packing n = 60 mit einer Kapazität und drei Familien. Gemessen ist weder irace noch HyFlex noch ein echtes Sprachmodell. Die Aussagen gelten nicht für große Budgets, andere Zielfunktionen oder andere Aufgaben.
* **N\\* gilt für Instanzen aus derselben Verteilung wie das Training.** Beim Verteilungswechsel ist die Auszahlung nicht mehr gesichert: In der Demo zum Verteilungswechsel war die erzeugte Einplanungsregel (GP, 16 000 Auswertungen) nach einem Familienwechsel in keiner der 72 Zellen besser als ATC(k) (Zeile der Karte in Frage 4). Die Lebensdauer R in Frage 2 rechnet den Wechsel als Obergrenze der Zahl nutzbarer Instanzen.
* **Die Meta-Ebene ist nirgends abgestimmt:** Lernraten, Populationsgrößen und Gewichtsuntergrenzen sind feste, nicht abgestimmte Setzungen. Das kann die Meta-Ebene benachteiligen; die Gegner haben null bis zwei Parameter (Zufallsauswahl und Best Fit keinen, ATC(k) einen, PR2 zwei), und ihre Einstellung kostet Auswertungen.
* **Die Teilmenge T3 wurde nachträglich gewählt,** nach Ansicht der Ergebnisse; ihre Kosten null verschweigen die Kosten der Erkenntnis.
* **Bei kleinem Gewinn ist N\\* unsicher:** Es streut über die 5 Wiederholungen schon in einer Zelle um mehr als das Dreifache (Rekord-zu-Rekord, 50·n, gleich/30, K = 3: 15,3 bis 52,9; K = 1: 4,6 bis 74,2, mehr als das 16-Fache); das Runden von Q_M auf zwei Stellen verschiebt N\\* in diesen Daten höchstens um das 1,17-Fache. Die Demo zeigt deshalb die Spanne über die Wiederholungen. N\\* ist nur definiert, wo der Gegner mit mehr Auswertungen verlässlich besser wird: auf der Rundtour ja (die Kurve der Zufallsauswahl fällt in allen sechs Zellen mit dem Budget); bei Einplanung und Bin Packing sind nur wenige Rasterpunkte des Gegners gemessen, sein Verlauf ist dort nicht durchgehend fallend, und die Demo bietet dort kein Break-even an.
* **Zähleinheit:** Auswertungen sind je Fahrzeug anders definiert, es gibt keinen Faktor über Fahrzeuge. Gleiche Auswertungszahl ist nicht gleiche Rechenzeit (Branke u. a. 2016); Zeiten sind hier nie ein Befund.
* **Nicht gemessen:** eine Menge ohne dominante Zugart, Budgets über 1 000 Auswertungen bei Bin Packing als Zählung, Late Acceptance mit anderer Listenlänge für N\\*, die Zustandsabhängigkeit der Auswahl, die Abstimmung der Meta-Ebene und der Nutzen im Betrieb. Die Aussagen sind keine Nutzenbehauptung für Logistik, Lager oder Fertigung: die drei Modelle sind erzeugt.
""".strip()

FORMEL_LESEHILFE = (
    "Gegeben sind eine Aufgabenklasse mit Instanzverteilung, ein Einsatzbudget je Instanz und eine Zahl N künftiger Instanzen; gesucht ist, ab welchem N die Meta-Ebene mit ihren "
    "Entwicklungskosten weniger Auswertungen braucht als der feste Gegner mit derselben Gesamtzahl und dabei nicht schlechter ist. Die Symbole stehen in der Tabelle unter den Formeln."
)

FORMEL_BLOECKE = [
    ("Gesamtkosten der Meta-Ebene (Auswertungen, je Fahrzeug in dessen Einheit):", r"C_M(N) = E_M + N\,b_M"),
    ("Gesamtkosten des festen Gegners:", r"C_F(N) = e_F + N\,b_F"),
    ("Der Gegner hat die Gütekurve $Q_F(\\beta)$: mittlerer Abstand zur Referenz in Prozent bei Einsatzbudget $\\beta$ je Instanz (kleiner ist besser). Bei gleicher Gesamtzahl $C_F(N) = C_M(N)$ und $b_F = \\beta$ darf der Gegner je Instanz ausgeben:",
     r"\beta'(N) = b_M + \frac{E_M - e_F}{N}"),
    ("Der **Break-even** ist die kleinste ganze Zahl $N$, bei der die Meta-Ebene mit ihrem Abstand $Q_M(b_M)$ nicht schlechter ist als der Gegner mit $\\beta'(N)$:",
     r"N^{*} = \min\{\, N \in \mathbb{N} : Q_M(b_M) \le Q_F(\beta'(N)) \,\}"),
    ("$Q_F$ fällt mit dem Budget, $\\beta'(N)$ fällt mit $N$: die Bedingung gilt für alle $N \\ge N^{*}$. Mit $\\beta^{*}$ als Lösung von $Q_F(\\beta^{*}) = Q_M(b_M)$ folgt:",
     r"N^{*} = \frac{E_M - e_F}{\beta^{*} - b_M}"),
    ("Zwischen den Stützstellen $\\beta_i$ der gemessenen Kurve ($\\beta_i \\in \\{1, 1{,}5, 2, 3, 4, 6, 8, 12, 16, 24, 32\\}\\cdot\\ell$) ist $Q_F$ linear in $\\ln \\beta$:",
     r"Q_F(\beta) = Q_i + \frac{\ln\beta - \ln\beta_i}{\ln\beta_{i+1} - \ln\beta_i}\,\bigl(Q_{i+1} - Q_i\bigr), \qquad \beta_i \le \beta \le \beta_{i+1}"),
    ("Rundtour: Kontrollstufe $\\ell = 50\\,n$ Auswertungen (groß: $4\\ell = 200\\,n$); Entwicklungskosten der gelernten Mischung $E_M = K\\,\\ell$, der gelernten Einzelheuristik $E_M = 8K\\,\\ell$, $e_F = 0$. Aufschlag der Meta-Ebene gegen den Gegner mit gleichem Einsatz:",
     r"\alpha(N) = \frac{C_M(N)}{N\,b_M} = 1 + \frac{E_M}{N\,b_M}"),
    ("Abstand zur Referenz der Rundtour in Prozent, mit der besten bekannten Tour $c_{\\mathrm{ref}}$ (nicht als optimal bewiesen):", r"Q = 100\,\frac{c - c_{\mathrm{ref}}}{c_{\mathrm{ref}}}"),
    ("Einplanung: Regret als Anteil mit den Kosten $c_i = \\sum_j w_j T_j$, $T_j = \\max(0, C_j - d_j)$ der Instanz $i$:", r"\rho = \frac{\sum_i c_i(\text{Regel})}{\sum_i c_i(\text{Referenz})} - 1"),
    ("Bin Packing: Überschuss über die untere Schranke mit der Behälterzahl $B$ und $\\mathrm{LB} = \\lceil \\sum_j s_j / C \\rceil$:", r"\ddot u = \overline{B/\mathrm{LB}} - 1"),
]

FORMEL_TABELLE = r"""
| Symbol | Bedeutung |
|---|---|
| $E_M$, $e_F$ | Entwicklungskosten der Meta-Ebene bzw. Einstellkosten des festen Gegners (Auswertungen, einmalig) |
| $b_M$, $b_F$ | Einsatzkosten je neue Instanz (Rundtour: Auswertungen; Einplanung und Bin Packing: Instanzläufe, 20 Instanzläufe sind 1 Auswertung) |
| $N$ | Zahl künftiger Instanzen aus derselben Verteilung wie das Training |
| $Q_M$, $Q_F(\beta)$ | mittlerer Abstand zur Referenz in Prozent: Meta-Ebene bei Einsatz $b_M$; Gegner bei Einsatzbudget $\beta$ |
| $\beta'(N)$, $\beta^{*}$ | Budget je Instanz, das der Gegner bei gleicher Gesamtzahl ausgeben darf; Budget, bei dem er den Abstand der Meta-Ebene erreicht |
| $N^{*}$ | Break-even (kleinste ganze Zahl); „nie“ und „über der Kurve“ sind Sonderfälle |
| $\ell$, $K$ | Länge der Kontrollstufe $50\,n$; Zahl der Trainingsinstanzen (1, 3, 10, 30) |
| $\alpha(N)$ | Aufschlag der Gesamtkosten gegen den Einsatz allein |
"""

FORMEL_SCHLUSS = (
    "Es gibt **keinen** Break-even („nie“), wenn $Q_M(b_M) \\ge Q_F(b_M)$, also kein Gewinn bei gleichem Einsatzbudget; und **keine Zahl** („über der Kurve“), wenn $Q_M(b_M)$ unter dem Wert der letzten "
    "Stützstelle $32\\,\\ell$ liegt, der Gewinn also größer ist, als die gemessene Kurve abdeckt. Das Modell ist vollständig für die Bilanz; die Verfahren selbst (Auswahlregeln, GP, Platzierungsregeln) "
    "stehen in den Demos der Reihe. Was fehlt und wie die Demo es umsetzt: (a) $Q_F$ ist nur für die Rundtour als Kurve über 11 Stützstellen gemessen; für Einplanung (ATC(k) mit 11, 41, 81 und 161 Werten) und Bin Packing (PR2 mit 64, 256 und 1 024 Auswertungen) gibt es nur wenige Rasterpunkte des Gegners, und sein Verlauf ist dort nicht durchgehend fallend; ein Break-even wird dort nicht angezeigt. (b) $Q_F$ ist ein Mittel über Zellen und Instanzen; $N^{*}$ "
    "ist ein Zahlenwert je Zelle mit Spanne über die Wiederholungen. (c) Die Einheit der Auswertung ist je Fahrzeug anders."
)

LITERATUR = (
    "**Literatur** (Belegstufen aus der Literaturrecherche zu dieser Reihe): Branke u. a. 2016 (IEEE Transactions on Evolutionary Computation, Übersicht zur Erzeugung von "
    "Prioritätsregeln: Vergleich bei gleicher Auswertungszahl hat begrenzte Gültigkeit); Burke u. a. 2013 (Journal of the Operational Research Society, Übersicht zu Hyperheuristiken); "
    "Sobotka u. a. (Vorabdruck arXiv 2509.02782); Sim, Renau, Hart (arXiv 2501.11411); Herrmann, Pallez (arXiv 2510.27353); Rice 1976 (Algorithmenauswahl)."
)
