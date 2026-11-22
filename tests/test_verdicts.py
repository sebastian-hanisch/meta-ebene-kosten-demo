"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Schwelle und jede Zahl im Text steht hier."""

import pytest

import mek_evaluation as ev

EH = "Auswertungen (Regel auf 20 Trainingsinstanzen)"


def test_kosten_anker_warning_an_der_grenze_ein_achtel():
    kind, text = ev.verdict_kosten("GP", "ATC(k) mit 11 Werten", 16000 / 11, 16000, 11, EH, 1, 4, 3, 8)     # 1 von 8: die Grenze 1/8 ist erreicht
    assert kind == "warning"
    assert "das 1 455-Fache" in text and "(16 000 gegen 11; Einheit: " + EH + ")" in text and "in 1 von 8 Zellen besser, in 4 gleich, in 3 schlechter" in text


def test_kosten_schwellen():
    assert ev.verdict_kosten("A", "B", 50.0, 500, 10, "E", 2, 3, 3, 8)[0] == "info"        # 2 von 8 > 1/8
    assert ev.verdict_kosten("A", "B", 9.9, 99, 10, "E", 0, 4, 4, 8)[0] == "info"          # Faktor unter 10: nie warning
    assert ev.verdict_kosten("A", "B", 10.0, 100, 10, "E", 0, 4, 4, 8)[0] == "warning"     # Faktor genau 10
    assert ev.verdict_kosten("A", "B", 50.0, 500, 10, "E", 4, 2, 2, 8)[0] == "success"     # genau die Hälfte
    assert ev.verdict_kosten("A", "B", 50.0, 500, 10, "E", 3, 2, 3, 8)[0] == "info"
    with pytest.raises(ValueError):
        ev.verdict_kosten("A", "B", 2.0, 2, 1, "E", 1, 1, 1, 8)                           # Zählung teilt die Zellen nicht auf


def test_kosten_zahlenformat():
    assert ev.faktor_text(15.625) == "15,6" and ev.faktor_text(99.4) == "99,4" and ev.faktor_text(1454.5) == "1 455" and ev.faktor_text(363.6) == "364"
    assert ev.tsd(46500) == "46 500" and ev.dez(1.5, 2) == "1,50" and ev.pp(-0.5) == "−0,50" and ev.pp(0.719) == "+0,72"


def test_aufschlag_text():
    kind, text = ev.verdict_aufschlag("die gelernte Mischung (K = 10)", 30, 15000, 1500, "Auswertungen")
    assert kind == "info" and "60 000 Auswertungen (15 000 Training plus 30 mal 1 500 Einsatz" in text and "das 1,33-Fache" in text
    with pytest.raises(ValueError):
        ev.verdict_aufschlag("x", 0, 1, 1, "e")


def _z(lohnt, zellen, gewinn, nie=0, mittel=None):
    return {"zellen": zellen, "lohnt": lohnt, "mittel": lohnt if mittel is None else mittel, "nie_zellen": nie, "gewinn": gewinn}


def test_breakeven_schwellen_und_anker():
    f = lambda z, **kw: ev.verdict_breakeven(z, kw.get("n", 30), "mix", 3, "rr", "50·n", kw.get("r"))      # noqa: E731
    assert f(_z(4, 6, 0.78))[0] == "success"                  # 4/6 = 2/3
    assert f(_z(3, 6, 0.78))[0] == "info"
    assert f(_z(1, 6, 0.78))[0] == "warning"                  # 1/6
    assert f(_z(0, 6, -0.3, nie=6))[0] == "warning"
    assert f(_z(4, 6, 0.24))[0] == "info"                     # Gewinn unter der Marke 0,25
    assert f(_z(6, 6, 0.25))[0] == "success"                  # Marke ist inklusive
    kind, text = f(_z(4, 6, 0.785, nie=1))
    assert "in 4 von 6 Zellen in allen Wiederholungen, in 1 Zellen in keiner Wiederholung" in text and "+0,79 Prozentpunkte" in text and "Voraussetzung: Instanzen aus derselben Verteilung" in text
    assert "Einsatz 50·n Auswertungen je Instanz" in text and "K = 3" in text


def test_breakeven_einzelne_zelle_nie_info_und_lebensdauer():
    assert ev.verdict_breakeven(_z(1, 1, 0.5), 30, "mix", 1, "rr", "50·n")[0] == "success"
    assert ev.verdict_breakeven(_z(1, 1, 0.1), 30, "mix", 1, "rr", "50·n")[0] == "warning"      # Gewinn unter der Marke
    assert ev.verdict_breakeven(_z(0, 1, 0.5), 30, "mix", 1, "rr", "50·n")[0] == "warning"
    text = ev.verdict_breakeven(_z(1, 1, 0.5), 30, "mix", 1, "rr", "50·n", "10")[1]
    assert "Das Training hält nur 10 Instanzen, gerechnet wird mit N = 10." in text
    assert "hält nur" not in ev.verdict_breakeven(_z(1, 1, 0.5), 5, "mix", 1, "rr", "50·n", "10")[1]


def test_erzeugen():
    k, t = ev.verdict_erzeugen("GP", "ATC(k)", 1454.5, 1, 4, 3, 8, 89.0, 31.0)
    assert k == "warning" and "das 1 455-Fache" in t and "in 89 % der Läufe" in t and "in 31 %" in t and "1 / 4 / 3 Zellen" in t
    assert ev.verdict_erzeugen("GP", "ATC(k)", 1454.5, 1, 4, 3, 8, 89.0, 70.0)[0] == "info"           # Lücke nicht über 20
    assert ev.verdict_erzeugen("GP", "ATC(k)", 1454.5, 1, 4, 3, 8, 89.0, 69.0)[0] == "info"           # Lücke genau 20: nicht größer
    assert ev.verdict_erzeugen("GP", "ATC(k)", 1454.5, 1, 4, 3, 8, 89.0, 68.9)[0] == "warning"
    assert ev.verdict_erzeugen("GP", "ATC(k)", 1454.5, 2, 3, 3, 8, 89.0, 31.0)[0] == "info"           # 2 von 8 > 1/8
    assert ev.verdict_erzeugen("GP", "ATC(k)", 10.0, 4, 2, 2, 8, 50.0, 50.0)[0] == "success"


ZEILE_L = dict(art="lohnt", meta_ebene="gelernte Mischung (K = 3)", gegner="Zufallsauswahl", fahrzeug="Rundtour", bedingung="rr, klein", k=5, m=6, k_mittel=6,
               einheit="Auswertung = bewerteter Kandidat", regel="Break-even: N* ≤ 30", voraussetzung="6 Zellen")
ZEILE_B = dict(ZEILE_L, art="bgs", b=1, g=4, s=3, m=8)


def test_karte():
    assert ev.verdict_karte(ZEILE_L)[0] == "success"
    assert ev.verdict_karte(dict(ZEILE_L, k=4))[0] == "success" and ev.verdict_karte(dict(ZEILE_L, k=3))[0] == "info" and ev.verdict_karte(dict(ZEILE_L, k=1))[0] == "warning"
    text = ev.verdict_karte(ZEILE_L)[1]
    assert "lohnt in 5 von 6 Zellen (im Mittel der Wiederholungen in 6)" in text and "Einheit: Auswertung = bewerteter Kandidat" in text and "Entscheidungsregel: Break-even" in text
    assert ev.verdict_karte(ZEILE_B)[0] == "warning" and ev.verdict_karte(dict(ZEILE_B, b=2))[0] == "info" and ev.verdict_karte(dict(ZEILE_B, b=4, g=2, s=2))[0] == "success"
    assert "besser in 1 von 8 Zellen, gleich in 4, schlechter in 3" in ev.verdict_karte(ZEILE_B)[1]
    k, t = ev.verdict_karte(dict(ZEILE_L, art="nicht_gemessen", voraussetzung="nicht gemessen: Grund"))
    assert k == "info" and "nicht gemessen" in t
    assert ev.zaehlung_text(ZEILE_B) == "1 / 4 / 3 von 8" and ev.zaehlung_text(ZEILE_L) == "lohnt in 5 von 6 (Mittel: 6)"


def test_zeit():
    k, t = ev.verdict_zeit({"a": 1.0, "b": 1.25})
    assert k == "warning" and "das 1,25-Fache" in t and "Branke u. a. 2016" in t        # Marke inklusive
    assert ev.verdict_zeit({"a": 1.0, "b": 1.2499})[0] == "info"
    assert ev.verdict_zeit({"a": 0.0, "b": 1.0})[0] == "info"                           # Uhr zu grob: keine Division durch null
    assert ev.verdict_zeit({"a": 2.0})[0] == "info"


def test_probe_auswertungen_nach_budget_von_hand():
    """ℓ = 50·30 = 1 500; Einsatz 8 Instanzen × 2 Läufe × 2 Varianten = 32 Läufe = 48 000; Training k·ℓ (Mischung) bzw. 9·k·ℓ (gelernte Einzelheuristik); k höchstens 3."""
    assert ev.probe_auswertungen_nach_budget("mix", 1) == 48000 + 1500 == 49500
    assert ev.probe_auswertungen_nach_budget("mix", 3) == 48000 + 4500 == 52500
    assert ev.probe_auswertungen_nach_budget("einzel", 1) == 48000 + 13500 == 61500
    assert ev.probe_auswertungen_nach_budget("einzel", 3) == 48000 + 40500 == 88500
    assert ev.probe_auswertungen_nach_budget("einzel", 30) == 88500                 # K wird auf 3 begrenzt


def test_probe_nominal_nahe_den_verbrauchten_auswertungen():
    res = ev.probe("rr", "mix", 1)
    soll = ev.probe_auswertungen_nach_budget("mix", 1)
    assert abs(res["kosten"] / soll - 1) < 0.05, (res["kosten"], soll)


def test_probe():
    assert ev.verdict_probe(0.5, 0.3, 8, "mix")[0] == "info" and "nicht von null zu unterscheiden" in ev.verdict_probe(0.5, 0.3, 8, "mix")[1]       # 0,5 < 2·0,3
    assert ev.verdict_probe(0.6, 0.3, 8, "mix")[0] == "success"                                                                                     # genau 2 Standardfehler
    assert ev.verdict_probe(-0.7, 0.3, 8, "einzel")[0] == "warning"
    assert "+0,60 ± 0,30" in ev.verdict_probe(0.6, 0.3, 8, "mix")[1] and "8 Testinstanzen" in ev.verdict_probe(0.6, 0.3, 8, "mix")[1]
