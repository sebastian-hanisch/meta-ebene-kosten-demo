"""AppTest: jedes Preset, die fünf Fragen mit ihren Verdikten, Probe und Zeitmessung, Permalink, Randwerte der Regler."""

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import mek_constants as C
import mek_presets as P

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))


def _app(query=None) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    if query:
        for k, v in query.items():
            at.query_params[k] = v
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _meldungen(at):
    return [m.value for kind in ("success", "info", "warning") for m in getattr(at, kind)]


def _erwartete_art(name):
    return {"Einplanung: GP gegen ATC(k)": "Genetische Programmierung", "Bin Packing: Regeln und Mengen": "EA-S und GP-T"}.get(name)


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_jedes_preset_laeuft_ohne_ausnahme_mit_allen_verdikten(name):
    at = _app()
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert not at.exception, [str(e) for e in at.exception]
    texte = _meldungen(at)
    assert any(t.startswith("Bei N = ") and "lohnt sich das Training" in t for t in texte)                 # Frage 2
    assert any("Entscheidungsregel:" in t or "nicht gemessen" in t for t in texte)                         # Frage 4
    assert len(at.dataframe) >= 4 and len(at.get("plotly_chart")) >= 3
    if _erwartete_art(name):
        assert any(_erwartete_art(name) in t and "kostet das" in t for t in texte), name                  # Frage 1 des gewählten Fahrzeugs


def test_frage_1_rundtour_nennt_gesamtkosten():
    at = _app()
    t = " ".join(_meldungen(at))
    assert "insgesamt" in t and "Einsatzes allein" in t


def test_permalink_uebernimmt_werte_und_rastet_ein():
    at = _app({"fz": "Einplanung", "k": "4", "n": "3", "g": "161", "zs": "5000", "akz": "la"})
    assert at.session_state["fahrzeug"] == "Einplanung" and at.session_state["rt_k"] == 3 and at.session_state["n_inst"] == 2
    assert at.session_state["ep_g"] == 161 and at.session_state["zeit_seed"] == C.SEED_MAX and at.session_state["h5_akz"] == "la"


def test_lebensdauer_kuerzer_als_n_wird_im_verdikt_genannt():
    at = _app()
    at.sidebar.selectbox(key="h5_r").set_value("10").run()
    assert not at.exception
    assert any("Das Training hält nur 10 Instanzen" in t for t in _meldungen(at))


def test_zeitknopf_misst_und_zeigt_verdikt():
    at = _app()
    at.button(key="knopf_zeit").click().run()
    assert not at.exception, [str(e) for e in at.exception]
    assert any("Bei gleicher Auswertungszahl" in t or "Uhr" in t for t in _meldungen(at))
    zeilen = [d for d in at.dataframe if "Sekunden je 1 000 Auswertungen" in list(d.value.columns)]
    assert zeilen and set(zeilen[0].value["Auswertungen"]) == {C.ZEIT_AUSWERTUNGEN}                       # Prüfzeile: gleiche Auswertungen in allen Zeilen


def test_probeknopf_rechnet_und_nennt_keine_n_stern_zahl():
    at = _app()
    at.button(key="knopf_probe").click().run()
    assert not at.exception, [str(e) for e in at.exception]
    t = " ".join(_meldungen(at))
    assert "Probe mit 8 Testinstanzen" in t and "Aus der Probe entsteht keine N*-Zahl" in t


@pytest.mark.parametrize("key,wert", [("n_inst", 2000), ("n_inst", 1), ("rt_k", 30), ("h5_zelle", "gleich/30"), ("h5_r", "10"), ("karte_fahrzeug", "Bin Packing"), ("karte_stabil", True)])
def test_randwerte_der_regler(key, wert):
    at = _app()
    spec = P.SETTING_SPECS[key]
    regler = None
    for art in ("select_slider", "selectbox", "toggle", "radio"):
        try:
            regler = getattr(at.sidebar, art)(key=key)
            break
        except KeyError:
            continue
    assert regler is not None, key
    regler.set_value(wert).run()
    assert not at.exception, (key, wert, [str(e) for e in at.exception])
    assert spec.options is None or wert in spec.options
