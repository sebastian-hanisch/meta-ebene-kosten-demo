"""End-to-end Smoke-Test via Streamlits AppTest (Vorlage tools/templates/test_app_smoke.py, angepasst an die Regler dieser Demo: Auswahlregler statt Schieberegler):
lädt app.py mit den Standardeinstellungen, klickt jeden Knopf und stellt jeden Regler auf seine Randwerte; es darf kein Python-Fehler auftreten, insbesondere nicht
`StreamlitDuplicateElementId` (mehrere Diagramme ohne eindeutiges key=)."""

import os

from streamlit.testing.v1 import AppTest

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))
AUTOPLAY_MARKER = "▶"  # Auto-Play-Knöpfe auslassen (die Probe-Knöpfe testen test_app_demo.py)


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def test_app_loads_without_exception():
    _fresh_app()


def test_every_button_click_does_not_raise():
    labels = [b.label for b in _fresh_app().button]
    assert labels, "keine Buttons gefunden"
    for index, label in enumerate(labels):
        if AUTOPLAY_MARKER in label:
            continue
        at = _fresh_app()
        at.button[index].click().run(timeout=TIMEOUT)
        assert not at.exception, (label, [str(e) for e in at.exception])


def test_every_select_slider_at_its_first_and_last_value_does_not_raise():
    keys = [s.key for s in _fresh_app().sidebar.select_slider]
    assert keys, "keine Auswahlregler gefunden"
    for key in keys:
        for edge in (0, -1):
            at = _fresh_app()
            regler = at.sidebar.select_slider(key=key)
            regler.set_value(regler.options[edge] if isinstance(regler.options[edge], (int, str)) else regler.value).run(timeout=TIMEOUT)
            assert not at.exception, (key, edge, [str(e) for e in at.exception])


def test_number_input_at_min_and_max_does_not_raise():
    keys = [s.key for s in _fresh_app().sidebar.number_input]
    assert keys, "keine Zahlenfelder gefunden"
    for key in keys:
        for edge in ("min", "max"):
            at = _fresh_app()
            feld = at.sidebar.number_input(key=key)
            feld.set_value(int(feld.min if edge == "min" else feld.max)).run(timeout=TIMEOUT)
            assert not at.exception, (key, edge, [str(e) for e in at.exception])
