"""Schreibt README.md: feste Abschnitte aus der Vorlage hier, alle Zahlen aus den eingefrorenen Dateien (data/mek_*.json), gerechnet mit denselben Funktionen wie die App.

    python tools/mek_readme.py            schreibt README.md
    python tools/mek_readme.py --check    prüft, dass README.md dem erzeugten Text entspricht

Die Testzahl der README wird mit `pytest --collect-only` ermittelt (nur beim Schreiben, nicht beim Prüfen der Zahlen)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import mek_constants as C  # noqa: E402
import mek_evaluation as E  # noqa: E402
import mek_frozen as F  # noqa: E402
import mek_kosten as KO  # noqa: E402
import mek_texts as TX  # noqa: E402
from mek_stats import mittel  # noqa: E402

FOOTER = (
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Hyperheuristiken: Auswählen und Erzeugen](https://sebastianhanisch.net/konzepte-hyperheuristiken.html)."
)


def lz(akz, art, k, stufe, n=30):
    z = F.zaehlung_lohnt(akz, "alle sechs", art, k, stufe, n)
    return z


def werte() -> dict:
    """Alle Zahlen der README aus den Dateien."""
    w = {}
    for akz in C.H5_AKZ:
        for stufe in C.STUFEN:
            for art, k in (("mix", 1), ("mix", 3), ("mix", 10), ("mix", 30), ("einzel", 3)):
                z = lz(akz, art, k, stufe)
                w[f"{akz}_{stufe}_{art}{k}"] = z
    w["kurve_lo"] = {akz: [F.rand_bei(akz, zn, "lo") for zn in F.zellen_namen("alle sechs")] for akz in C.H5_AKZ}
    w["wdh_je_zelle"] = F.h5()["meta"]["wiederholungen"]
    # kleinstes N* (aus dem Mittel der Wiederholungen) der gelernten Einzelheuristik, K = 3, Late Acceptance, klein
    ns = [F.stern("la", zn, "einzel", 3, "lo")["wert"] for zn in F.zellen_namen("alle sechs")]
    w["einzel_la_lo_min_n"] = min(x for x in ns if x is not None) if any(x is not None for x in ns) else None
    w["einzel_la_lo_status"] = [F.stern("la", zn, "einzel", 3, "lo")["status"] for zn in F.zellen_namen("alle sechs")]
    w["raster"] = E.raster_aenderung_ep()
    w["pr2"] = E.raster_aenderung_pr2()
    return w


def tabelle_n(akz, stufe, art, ks) -> str:
    z = {k: lz(akz, art, k, stufe) for k in ks}
    return ", ".join(f"K = {k}: {z[k]['lohnt']} von 6 (Mittel {z[k]['mittel']})" for k in ks)


def bauen(testzahl: str) -> str:
    w = werte()
    K = lambda akz, stufe, art, k: w[f"{akz}_{stufe}_{art}{k}"]  # noqa: E731
    pp = E.pp
    ra = w["raster"]
    g = {(b, gi): F.ep_zaehlung("gp", b, gi) for b in C.EP_B for gi in C.EP_RASTER}
    ft = {b: F.ep_gegen_fest(b) for b in C.EP_B}
    bs = {b: F.bp_suche_zaehlung(b) for b in C.BP_BUDGETS}
    karte = {r["id"]: r for r in F.karte()["zeilen"]}
    n_karte = len(F.karte()["zeilen"])
    n_nicht = sum(r["art"] == "nicht_gemessen" for r in F.karte()["zeilen"])
    pr2 = {gi: [F.bp_pr2_median(f, gi, "test") for f in C.BP_FAMILIEN] for gi in C.BP_PR2_GRID}
    pr2t = {gi: [F.bp_pr2_median(f, gi, "train") for f in C.BP_FAMILIEN] for gi in C.BP_PR2_GRID}
    ea = [F.bp_suche_median(f, "EA-S", 1000) for f in C.BP_FAMILIEN]
    eat = [F.bp_suche_median(f, "EA-S", 1000, "train") for f in C.BP_FAMILIEN]
    gain = lambda akz, stufe, k: mittel(F.gewinn(akz, zn, "mix", k, stufe) for zn in F.zellen_namen("alle sechs"))  # noqa: E731
    gr = lambda akz, stufe: (min(gain(akz, stufe, k) for k in C.H5_KS), max(gain(akz, stufe, k) for k in C.H5_KS))  # noqa: E731
    fmt3 = lambda xs: " / ".join(pp(x, 3) for x in xs)  # noqa: E731
    ep_tr = {r: (F.ep_anteil("gp", 16000, 11, "train", r), F.ep_anteil("gp", 16000, 11, "test", r)) for r in C.EP_REGIME}
    f1 = [KO.faktor(b, 11) for b in C.EP_B]
    f161 = [KO.faktor(b, 161) for b in C.EP_B]
    stern_min = w["einzel_la_lo_min_n"]
    stern_min_text = "keine Zelle mit endlichem N*" if stern_min is None else f"kleinstes N* {E.dez(stern_min, 1)}"
    bpm = {p: karte[f"bp-menge-{p}-orakel"] for p in ("Z-S", "EA-S", "GP-T")}
    bpf = {p: karte[f"bp-menge-{p}-merkmal"] for p in ("Z-S", "EA-S", "GP-T")}
    fw = {b: (karte[f"ep-wechsel-fam-{b}"]["b"], karte[f"ep-wechsel-fam-{b}"]["g"], karte[f"ep-wechsel-fam-{b}"]["s"]) for b in (16000, 4000, 1000)}
    on = {(r, a, s): karte[f"rt-online-{r}-{a}-{s}"] for r in ("cf", "laut", "q") for a in ("ob", "rr", "la") for s in ("klein", "gross")}
    t3 = {(a, j): karte[f"rt-t3-{a}-{j}"] for a in ("ob", "rr", "la") for j in range(3)}
    rr_hi = [K("rr", "hi", "mix", k)["lohnt"] for k in (1, 3, 10, 30)]
    la_hi_max = max(K("la", "hi", "mix", k)["lohnt"] for k in (1, 3, 10, 30))
    assert max(K("la", "lo", "mix", k)["lohnt"] for k in (1, 3, 10, 30)) == 0, "Text sagt: unter Late Acceptance mit kleinem Budget in keiner Zelle"
    ep_besser_regime = sorted({z.split("|")[0] for z in F.ep_zellen() if F.d1_urteil(F.ep_deltas(z, "gp", 16000, 11))["urteil"] == "besser"})
    assert ep_besser_regime == ["gross"], "Text sagt: die besseren Zellen sind alle im Regime groß"
    la_min = min((s["wert"], k, zn) for k in (1, 3, 10, 30) for zn in F.zellen_namen("alle sechs") for s in [F.stern("la", zn, "mix", k, "lo")] if s["status"] == "ok")
    h5_gesamt = F.h5()["meta"]["auswertungen_gesamt"]

    kopf = f"""# Lohnt die Meta-Ebene? Eine Kostenrechnung in Auswertungen

<!-- Live-Link nach dem Deploy: **[→ Demo live ausprobieren](https://sebastianhanisch-meta-ebene-kosten-demo.streamlit.app/)** -->

Eine **Hyperheuristik** wählt oder erzeugt Heuristiken, statt selbst eine Lösung zu suchen. Das kostet **Auswertungen**, bevor die erste Instanz gelöst ist: Training, Suche im Regelraum, mehrere Läufe je Instanz.
Diese Demo rechnet die Gesamtkosten der Meta-Ebene (Entwicklung plus N Einsätze) gegen eine feste Heuristik, die man hätte nehmen können, und fragt, ab wie vielen Instanzen sich der Aufwand auszahlt und ob überhaupt.
Sie ist der Zusammenfluss der Reihe „Hyperheuristiken erklärt“ (Bereich Optimierung, Feld Metaheuristiken und Suche) und rechnet an drei erzeugten Modellen: Rundtour, Einplanung (eine Maschine, gewichtete Verspätung) und Bin Packing (online).
Verweise auf andere Demos der Reihe nennen nur ihren Namen (Hyperheuristik, Zugmenge, Auswahlregeln, Akzeptanz mal Auswahl, Prioritätsregel-Evolution, Platzierungsfunktion, Regel-Verteilungswechsel, Heuristik-Variation).

## Kernfrage

**Die Meta-Ebene kostet Auswertungen, bevor die erste Instanz gelöst ist. In diesen Messungen (drei erzeugte Modelle, eigene Umsetzungen, kleine Budgets, Zähleinheit Auswertungen je Fahrzeug) zahlte sie sich nur unter bestimmten Bedingungen aus:
das Training der Auswahl auf der Rundtour zahlte sich bei N = 30 am ehesten unter Rekord-zu-Rekord mit kleinem Budget und kleinem K aus (K = 1: {K('rr', 'lo', 'mix', 1)['lohnt']} von 6 Zellen); unter Rekord-zu-Rekord mit großem Budget lohnte es sich in {rr_hi[0]} / {rr_hi[1]} / {rr_hi[2]} / {rr_hi[3]} von 6 Zellen (K = 1 / 3 / 10 / 30), unter Late Acceptance mit kleinem Budget in keiner Zelle, mit großem Budget in höchstens {la_hi_max} von 6; die Erzeugung von Regeln (GP) ist gegen ATC(k) mit 11 Werten bei 16 000 Auswertungen in {g[(16000, 11)][0]} von 8 Zellen besser (alle im Regime groß), in {g[(16000, 11)][2]} schlechter, wobei GP das {E.faktor_text(f1[2])}-Fache der Auswertungen von ATC mit 11 Werten braucht (das {E.faktor_text(f161[2])}-Fache bei 161 Werten); gierig zusammengestellte Mengen der Größe k = 3 (Bin Packing, drei Pools, drei Familien) gewannen gegen Best Fit nur mit Orakelwahl (3 Läufe je Instanz), nicht mit der Merkmalswahl (1 Lauf).
Das ist ein Befund für diese Messbereiche und diese Umsetzungen, keine Aussage über Hyperheuristiken im Allgemeinen und keine über irace, HyFlex oder Sprachmodelle.**

Das Rückgrat der Reihe: In den Messungen der Reihe hing es auf der Rundtour an der Akzeptanzregel und (nach dem Stück zur Zugmenge, mit einer nachträglich gewählten Teilmenge) an der Zugmenge ab, ob Lernen hilft; bei Einplanung und Bin Packing sind feste Gegner (ATC(k) mit eingestelltem k, Best Fit ohne Einstellung) stark, und die Meta-Ebene kostet ein Vielfaches an Auswertungen.

Hook als Befund (Rundtour, 6 Zellen, 30 Testinstanzen × 5 Läufe, {w['wdh_je_zelle']} Wiederholungen des Trainings, Einsatz 50·n Auswertungen je Instanz, Mischung): unter Rekord-zu-Rekord lohnt sich das Training der Auswahl bei N = 30 Instanzen in allen Wiederholungen für {tabelle_n('rr', 'lo', 'mix', (1, 3, 10, 30))}; unter Late Acceptance lohnt es sich mit diesem Budget bei N = 30 in keiner Zelle ({tabelle_n('la', 'lo', 'mix', (1, 3, 10, 30))}; kleinstes N* im Mittel der Wiederholungen {E.dez(la_min[0], 1)} Instanzen bei K = {la_min[1]} in {la_min[2]}), mit großem Budget (200·n) in höchstens {la_hi_max} von 6 Zellen.
Das K der Antwort ist selbst ein Teil des Befunds.
"""
    korr = f"""
## Befunde und Korrekturen gegenüber der Vormessung

Die Vormessung der Planung rechnete mit `numpy.default_rng`, 3 Wiederholungen des Trainings und dem Mittel der Wiederholungen für N*; diese Demo rechnet mit SplitMix64, {w['wdh_je_zelle']} Wiederholungen und je Wiederholung ein eigenes N*. Was sich verschoben hat:

* **Training der Auswahl, Rekord-zu-Rekord, klein (50·n):** Der Gewinn bei gleichem Einsatz liegt bei {pp(gain('rr', 'lo', 1))} (K = 1), {pp(gain('rr', 'lo', 3))} (K = 3), {pp(gain('rr', 'lo', 10))} (K = 10) und {pp(gain('rr', 'lo', 30))} Prozentpunkten (K = 30), die Vormessung nannte +0,72 bis +0,83. K = 10, die vorab festgelegte Wahl, lohnt sich nach dem Mittel der Wiederholungen in {K('rr', 'lo', 'mix', 10)['mittel']} von 6 Zellen (Vormessung 0 von 6), in allen Wiederholungen in {K('rr', 'lo', 'mix', 10)['lohnt']}; die Regel „N* ≤ 30 in mindestens 4 von 6 Zellen“ ist damit auch jetzt nicht erfüllt.
* **Groß (200·n):** Der Gewinn bei gleichem Einsatz liegt unter Rekord-zu-Rekord für K = 1 bis 30 zwischen {pp(gr('rr', 'hi')[0])} und {pp(gr('rr', 'hi')[1])} Prozentpunkten (Vormessung höchstens +0,15), also um die Marke von 0,25 herum.
* **Late Acceptance, klein:** Das Training lohnt sich in 0 von 6 Zellen für jedes K (wie in der Vormessung); der Gewinn bei gleichem Einsatz ist für K = 1 bis 30 negativ ({pp(gr('la', 'lo')[0])} bis {pp(gr('la', 'lo')[1])} Prozentpunkte).
* **Gelernte Einzelheuristik, Late Acceptance, K = 3, klein:** lohnt sich in {K('la', 'lo', 'einzel', 3)['lohnt']} von 6 Zellen ({stern_min_text}; Vormessung: kleinstes N* 80,8).
* **GP gegen ATC(k), 16 000 Auswertungen, 8 Zellen (besser / gleich / schlechter, Regel D1):** {g[(16000, 11)][0]} / {g[(16000, 11)][1]} / {g[(16000, 11)][2]} gegen ATC mit 11 Werten (Vormessung 1 / 4 / 3), {g[(16000, 161)][0]} / {g[(16000, 161)][1]} / {g[(16000, 161)][2]} gegen ATC mit 161 Werten (Vormessung 1 / 4 / 3; für 81 Werte 1 / 3 / 4). Ein feineres Raster macht den Gegner nicht verlässlich besser: der Median seines Regrets ändert sich um {pp(ra['minimum'])} bis {pp(ra['maximum'])} Prozentpunkte (negativ = besser; besser in {ra['besser']}, schlechter in {ra['schlechter']} von 8 Zellen).
* **Bin Packing:** Die erzeugten Regeln (7 Suchverfahren) sind gegen Best Fit in 0 von 21 Zellen besser, in {bs[1000][2]} schlechter (200 und 1 000 Auswertungen; die Vormessung zählte 0 von 27). PR2 mit 256 und 1 024 statt 64 Auswertungen: Median Δ auf frischen Instanzen {fmt3(pr2[16])} und {fmt3(pr2[32])} (64: {fmt3(pr2[8])}) Prozentpunkte, alle 9 Zellen nach der Regel „gleich“. {E.text_pr2_schwelle()} Auf dem Training wird PR2 besser (64 Auswertungen {fmt3(pr2t[8])}, 1 024 Auswertungen {fmt3(pr2t[32])}).
* **Faktoren:** {E.faktor_text(f1[0])}, {E.faktor_text(f1[1])} und {E.faktor_text(f1[2])} (1 000, 4 000, 16 000 Auswertungen gegen 11), gegen 161 Werte {E.faktor_text(f161[0])}, {E.faktor_text(f161[1])} und {E.faktor_text(f161[2])} (der Zuschnitt rundete „90 bis 1 450“).
* **Übernommen aus den Demos der Reihe (Stand der Texte nach deren Aussagenprüfung):** Familienwechsel der Einplanung bei 16 000 Auswertungen {fw[16000][2]} von 72 Zellen schlechter, {fw[16000][1]} gleich, {fw[16000][0]} besser (Vormessung 61 von 72); Packen, Familienwechsel (fünf Suchverfahren über Bäume und Schablonen, 1 000 Auswertungen): 13 von 30 Zellen schlechter als Best Fit, 17 gleich, 0 besser; unter Rekord-zu-Rekord bei 50·n gewinnen Choice Function, Lernautomat und Q-Lernen gegen die Zufallsauswahl ({pp(on[('cf', 'rr', 'klein')]['mittel'])} / {pp(on[('laut', 'rr', 'klein')]['mittel'])} / {pp(on[('q', 'rr', 'klein')]['mittel'])} Prozentpunkte im Mittel über 6 Zellen, Zählung nach Zellenmitteln gegen die Marke 0,25), unter Late Acceptance verlieren sie; die gierig zusammengestellte Menge mit Orakelwahl gewinnt auch aus dem Pool der Zufallssuche.
* **Klassenmarken:** Stück 1 ist die Quelle (0,25 und 0,10 Prozentpunkte); die Demos zur Zugmenge und zu den Auswahlregeln zählen etwas anders. Diese Demo zählt Zellenmittel gegen die Marke 0,25 ohne Intervall.
"""
    modell = """
## Modell

Gesamtkosten der Meta-Ebene C_M(N) = E_M + N·b_M, des festen Gegners C_F(N) = e_F + N·b_F. Bei gleicher Gesamtzahl darf der Gegner je Instanz β′(N) = b_M + (E_M − e_F)/N ausgeben; der **Break-even** N* ist die kleinste Zahl Instanzen, bei der die Meta-Ebene mit ihrem Abstand nicht schlechter ist als der Gegner mit β′(N). Ist Q_M(b_M) ≥ Q_F(b_M), gibt es kein N* („nie“). Die Gütekurve des Gegners ist zwischen den Stützstellen (1, 1,5, 2, 3, 4, 6, 8, 12, 16, 24, 32 mal ℓ = 50·n) linear in ln β. Alle Formeln und die Symboltabelle stehen im Expander „📐 Mathematische Formulierung“ der App.
Die Einheit der Auswertung ist je Fahrzeug eine andere; es gibt keinen Faktor über Fahrzeuge.
"""
    meth = f"""
## Methodik

* **Rundtour** (n = 30 und 60, Familien gleichverteilt, Gruppen, Gitter; 8 Zugarten; Zufall SplitMix64): 6 Zellen, je 30 Testinstanzen × 5 Läufe, zwei Akzeptanzregeln (Rekord-zu-Rekord, Late Acceptance mit L = 50). Training: gelernte Mischung (ein Lauf der Zufallsauswahl je Trainingsinstanz, Gewicht = mittlere Belohnung je Anwendung, Untergrenze 0,02) und gelernte Einzelheuristik (alle acht einzeln), K = 1, 3, 10, 30 Trainingsinstanzen, {w['wdh_je_zelle']} Wiederholungen. Gegner: Zufallsauswahl über alle acht Zugarten mit einer Budgetkurve bis 32·ℓ. Referenz je Instanz: Minimum aus den Langläufen der Zugmenge-Demo und allen Läufen dieser Messung (nicht als optimal bewiesen).
* **Einplanung** (1‖ΣwⱼTⱼ, Training mit n = 10 bzw. 40, 20 Trainingsinstanzen, 4 Familien, 20 Läufe je Zelle): die Läufe von GP, (1+1) und Zufallssuche stammen aus der Demo zu den Prioritätsregeln; neu gerechnet ist der Gegner ATC(k) mit k aus 11, 41, 81 und 161 Werten (11 Werte: das Raster der Quelle, ungefähr geometrisch von 0,1 bis 6,0, es reproduziert deren Läufe; 41, 81 und 161 Werte: geometrisch von 0,1 bis 6,0).
* **Bin Packing** (n = 60, Kapazität 100, 3 Familien, 20 Trainingsinstanzen, Test 200 Instanzen, 20 Läufe): die Läufe der Suchverfahren aus der Demo zu den Platzierungsfunktionen, die Mengen aus der Demo zur Heuristik-Variation; neu gerechnet ist PR2 auf Gittern von 8 × 8, 16 × 16 und 32 × 32 (reproduziert für 8 × 8 die Quelle).
* **Zähleinheit** (Frage 1): Rundtour ein bewerteter Kandidat; Einplanung und Bin Packing eine Regel auf der Trainingsmenge von 20 Instanzen, ein Einsatz je Instanz ist 1/20 Auswertung. Zeiten sind nie ein Befund.
* **Vorgerechnet und eingefroren:** `data/mek_h5.json` (Rundtour, rund {round(h5_gesamt / 1e6)} Millionen Auswertungen nach den Budgets gerechnet, nicht gezählt; `tools/mek_make_h5.py`), `data/mek_gegner.json` (`tools/mek_make_gegner.py`), `data/mek_karte.json` und `data/mek_kosten.json` (`tools/mek_make_karte.py`). Live rechnet die App nur die Probe von Frage 2 und die Zeitmessung von Frage 5.
"""
    befunde = f"""
## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen mit Voraussetzung im selben Satz; die Spalte „Test“ nennt die Prüfung (`tests/test_claims.py`, Band oder exakt).

| Frage | Befund | Test |
|---|---|---|
| Kosten (Faktor) | GP braucht {E.faktor_text(f1[0])}-, {E.faktor_text(f1[1])}- und {E.faktor_text(f1[2])}-mal so viele Auswertungen wie ATC(k) mit 11 Werten (1 000, 4 000, 16 000 gegen 11 Auswertungen), {E.faktor_text(f161[0])}-, {E.faktor_text(f161[1])}- und {E.faktor_text(f161[2])}-mal gegen 161 Werte | `test_faktoren`, exakt |
| Break-even, Rundtour | Rekord-zu-Rekord, 50·n, Mischung, N = 30, 6 Zellen, {w['wdh_je_zelle']} Wiederholungen: {tabelle_n('rr', 'lo', 'mix', (1, 3, 10, 30))} (in allen Wiederholungen; in Klammern das Mittel der Wiederholungen) | `test_lohnt_zaehlung`, exakt auf der Datei, Neurechnung als Band |
| Break-even, Late Acceptance | Late Acceptance, 50·n, Mischung, N = 30: {tabelle_n('la', 'lo', 'mix', (1, 3, 10, 30))} | `test_lohnt_zaehlung` |
| Break-even, groß | Rekord-zu-Rekord, 200·n, Mischung, N = 30: {tabelle_n('rr', 'hi', 'mix', (1, 3, 10, 30))}; Late Acceptance, 200·n: {tabelle_n('la', 'hi', 'mix', (1, 3, 10, 30))} | `test_lohnt_zaehlung` |
| Gelernte Einzelheuristik | K = 3, N = 30, 50·n: Rekord-zu-Rekord {K('rr', 'lo', 'einzel', 3)['lohnt']} von 6, Late Acceptance {K('la', 'lo', 'einzel', 3)['lohnt']} von 6 | `test_lohnt_zaehlung` |
| Gewinn bei gleichem Einsatz | Rekord-zu-Rekord, 50·n, Mittel über 6 Zellen und {w['wdh_je_zelle']} Wiederholungen: {pp(gain('rr', 'lo', 1))} / {pp(gain('rr', 'lo', 3))} / {pp(gain('rr', 'lo', 10))} / {pp(gain('rr', 'lo', 30))} Prozentpunkte für K = 1 / 3 / 10 / 30; bei 200·n {pp(gain('rr', 'hi', 1))} / {pp(gain('rr', 'hi', 3))} / {pp(gain('rr', 'hi', 10))} / {pp(gain('rr', 'hi', 30))} | `test_gewinn`, Band |
| GP gegen ATC(k) | 8 Zellen, 20 Läufe, Regel D1, 16 000 Auswertungen: {g[(16000, 11)][0]} / {g[(16000, 11)][1]} / {g[(16000, 11)][2]} (11 Werte), {g[(16000, 41)][0]} / {g[(16000, 41)][1]} / {g[(16000, 41)][2]} (41), {g[(16000, 81)][0]} / {g[(16000, 81)][1]} / {g[(16000, 81)][2]} (81), {g[(16000, 161)][0]} / {g[(16000, 161)][1]} / {g[(16000, 161)][2]} (161); 4 000 Auswertungen: {g[(4000, 11)][0]} / {g[(4000, 11)][1]} / {g[(4000, 11)][2]} (11), 1 000: {g[(1000, 11)][0]} / {g[(1000, 11)][1]} / {g[(1000, 11)][2]} (11) | `test_gp_gegen_atc`, exakt auf der Datei, mit scipy nachgerechnet |
| GP gegen feste Regeln | beste von SPT, EDD, WSPT, MDD je Zelle, 8 Zellen: 16 000 Auswertungen {ft[16000][0]} besser, 4 000 {ft[4000][0]} besser, 1 000 {ft[1000][0]} besser (nicht gegen ATC(k)) | `test_gp_gegen_atc` |
| Training gegen Test | GP, 16 000 Auswertungen, Anteil der Läufe unter ATC(k) mit 11 Werten: Training {E.dez(ep_tr['klein'][0], 0)} % (klein) und {E.dez(ep_tr['gross'][0], 0)} % (groß), frische Instanzen {E.dez(ep_tr['klein'][1], 0)} % und {E.dez(ep_tr['gross'][1], 0)} % | `test_gp_gegen_atc` |
| Raster des Gegners | 161 statt 11 k-Werte: Median des Regrets von ATC(k) ändert sich um {pp(ra['minimum'])} bis {pp(ra['maximum'])} Prozentpunkte (8 Zellen, 20 Läufe) | `test_gp_gegen_atc` |
| Bin Packing, Suche | 7 Suchverfahren × 3 Familien, 20 Läufe, Regel der Platzierungsfunktionen: bei 200 und bei 1 000 Auswertungen {bs[1000][0]} besser, {bs[1000][1]} gleich, {bs[1000][2]} schlechter von 21 Zellen | `test_bin_packing`, exakt auf der Datei |
| Bin Packing, PR2 | Median Δ gegen Best Fit auf frischen Instanzen (gleichverteilt / Häufungen / breit gestreut): {fmt3(pr2[8])} (64 Auswertungen), {fmt3(pr2[16])} (256), {fmt3(pr2[32])} (1 024); alle 9 Zellen nach der Regel „gleich“. {E.text_pr2_schwelle()} | `test_bin_packing` |
| Bin Packing, Training | EA-S, 1 000 Auswertungen, Median Δ Training / Test: {fmt3(eat)} / {fmt3(ea)} Prozentpunkte | `test_bin_packing` |
| Mengen | gierige Menge k = 3 gegen Best Fit, mit Orakelwahl (3 Läufe je Instanz): besser in {bpm['Z-S']['b']} von 3 Familien für jeden der Pools Zufallssuche, EA-S, GP-T; mit Merkmalswahl (1 Lauf) schlechter in {bpf['EA-S']['s']} von 3 | `test_karte_zeilen` |
| Verteilungswechsel | Familienwechsel, 16 000 Auswertungen: {fw[16000][0]} besser, {fw[16000][1]} gleich, {fw[16000][2]} schlechter von 72 Zellen (Zählung aus der Demo zum Verteilungswechsel) | `test_karte_zeilen` |
| Verteilungswechsel, Packen | Familienwechsel, fünf Suchverfahren über Bäume und Schablonen, 1 000 Auswertungen: 0 besser, 17 gleich, 13 schlechter von 30 Zellen gegen Best Fit (Zählung aus der Demo zum Verteilungswechsel) | `test_verteilungswechsel_packen`, nur mit dem Nachbarordner |
| Online gelernt | unter Rekord-zu-Rekord, 50·n, Mittel über 6 Zellen: Choice Function {pp(on[('cf', 'rr', 'klein')]['mittel'])}, Lernautomat {pp(on[('laut', 'rr', 'klein')]['mittel'])}, Q-Lernen {pp(on[('q', 'rr', 'klein')]['mittel'])} Prozentpunkte; unter Late Acceptance {pp(on[('cf', 'la', 'klein')]['mittel'])} / {pp(on[('laut', 'la', 'klein')]['mittel'])} / {pp(on[('q', 'la', 'klein')]['mittel'])} | `test_karte_zeilen` |
| Teilmenge T3 | gegen die volle Menge, nachträglich gewählt, Zellenmittel (besser / gleich / schlechter von 6): Rekord-zu-Rekord klein {t3[('rr', 0)]['b']} / {t3[('rr', 0)]['g']} / {t3[('rr', 0)]['s']}, nur besser klein {t3[('ob', 0)]['b']} / {t3[('ob', 0)]['g']} / {t3[('ob', 0)]['s']}, Late Acceptance klein {t3[('la', 0)]['b']} / {t3[('la', 0)]['g']} / {t3[('la', 0)]['s']} | `test_karte_zeilen` |
| Karte | {n_karte} Zeilen, davon {n_nicht} „nicht gemessen“ | `test_karte_zeilen` |
| Zeit | keine Zahl: die Zeitmessung ist eine Probe auf dem Rechner des Besuchers; getestet wird nur, dass alle Zeilen gleich viele Auswertungen haben | `test_app_demo` |

Messungen dieser README ohne Test: die Spannen der Wiederholungen je Zelle (stehen in der App-Tabelle), die Gewichte der gelernten Mischungen (`data/mek_h5.json`, nur auf Plausibilität geprüft).
"""
    grenzen = "\n## Ehrliche Grenzen\n\n" + TX.ASSUMPTIONS_MARKDOWN + "\n"
    plan = f"""
## Befunde und Korrekturen gegenüber dem Plan

* **Gegner mit Budgetkurve (Einplanung, Bin Packing):** Der Plan erwartete, dass mehr Auswertungen den Gegner nicht verbessern (GP gegen ATC(g) 1 / 4 / 3 bei 11, 41 und 161 Werten, 1 / 3 / 4 bei 81). Gemessen ist: GP steht gegen feinere Raster besser da ({g[(16000, 161)][0]} / {g[(16000, 161)][1]} / {g[(16000, 161)][2]} bei 161 Werten), und der Median des Regrets von ATC ändert sich je Zelle um {pp(ra['minimum'])} bis {pp(ra['maximum'])} Prozentpunkte. Die Demo sagt deshalb „nicht verlässlich besser“ und bietet für diese Fahrzeuge kein Break-even an.
* **Zahlen der Vormessung** wurden im Bau neu gemessen (siehe oben); die Zahlen der Demos der Reihe stammen aus deren eingefrorenen Dateien.
* **Experimente:** Alle fünf Fragen sind gebaut (Kostenbuch, Break-even mit Probe, Kosten-Nutzen der Erzeugung, Karte, Zeit). Der Plan sah ein Kostenbuch mit einer Zeile je COVERT, ATC2 und Impfung nicht vor; sie fehlen.
* **Karte:** Die Zeilen werden aus den Dateien gezählt; die Online-Zeilen (Choice Function, Lernautomat, Q-Lernen) und die Teilmengen-Zeilen zählen Zellenmittel gegen die Marke 0,25 Prozentpunkte (der Plan nannte die Zählung der Vormessung mit gd und sa; für sie liegen in den Demos der Reihe keine Zellenwerte vor).
* **Kopien:** Rundtour-Kern aus Stück 1 und 2 (`mek_scenario.py`, `mek_moves.py`, `mek_accept.py`, `mek_search.py`, `mek_rngblock.py`, `mek_select.py`, `mek_refs.json`) bytegleich bis auf das Präfix, `mek_rng.py` die Vorlage der Website; die Kopier-Tests überspringen sich ohne Nachbarordner. Der Kern von Einplanung und Bin Packing wird nicht kopiert: `tools/mek_make_gegner.py` liest ihn aus den Nachbardemos, der Neurechnen-Test dafür braucht sie.
"""
    tests = f"""
## Tests

{testzahl}. Zusammensetzung: Handwerte (Break-even, Kosten, Orakelwahl von Hand), Orakel (N* auf drei Wegen, unabhängiger Zähler der Auswertungen, Bilanz, Karte gegen die Quellen), Eigenschaften, Verdikte an gesetzten Werten, Kopier-Tests, Neurechnen als Band, Claims der README (`tests/test_claims.py`), Presets und Layout, App (jedes Preset, Probe, Zeit), Footer, Laufzeit-Importe. Die Neu-Rechnen-Tests sind Bänder, keine bitgleichen Vergleiche (C-Bibliothek und Summenreihenfolge unterscheiden sich zwischen Plattformen).
"""
    dateien = """
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
"""
    nicht = """
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
"""
    lokal = f"""
## Lokal ausführen

```
pip install -r requirements.txt
streamlit run app.py
```

Gebaut mit Streamlit, Plotly und NumPy.

Quellen (Belegstufen aus der Literaturrecherche der Reihe): Branke u. a. 2016 (V), Burke u. a. 2013 (V), Sobotka u. a. (V, Vorabdruck arXiv 2509.02782), Sim u. a. (V, arXiv 2501.11411), Herrmann und Pallez (V, arXiv 2510.27353), Rice 1976 (A).

{FOOTER}
"""
    return kopf + korr + modell + meth + befunde + grenzen + plan + tests + dateien + nicht + lokal


def testzahl_text() -> str:
    """Testzahl: Argument `--tests N`, sonst die Zahl der bisherigen README, sonst ein Platzhalter."""
    import re
    if "--tests" in sys.argv:
        return f"{int(sys.argv[sys.argv.index('--tests') + 1])} Tests"
    alt = ROOT / "README.md"
    if alt.exists():
        m = re.search(r"(\d+) Tests\. Zusammensetzung", alt.read_text(encoding="utf-8"))
        if m:
            return f"{m.group(1)} Tests"
    return "TESTZAHL Tests"


def main() -> None:
    text = bauen(testzahl_text())
    if "--check" in sys.argv:
        ok = (ROOT / "README.md").read_text(encoding="utf-8").replace("\r\n", "\n") == text
        print("README stimmt" if ok else "README weicht ab")
        sys.exit(0 if ok else 1)
    (ROOT / "README.md").write_text(text, encoding="utf-8", newline="\n")
    print("README geschrieben,", len(text), "Zeichen")


if __name__ == "__main__":
    main()
