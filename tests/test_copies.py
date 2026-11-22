"""Kopier-Tests: die Rundtour-Module sind wörtliche Kopien aus den Vorgänger-Demos der Reihe (Präfix ersetzt), der Zufall die Vorlage der Website.

Fehlt der Nachbarordner (CI), überspringen sich die Tests. Eine Korrektur gehört in die Quelle und wird mit tools/mek_kopien.py neu kopiert."""

import sys
from pathlib import Path

import pytest

import mek_constants as C

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import mek_kopien as KP  # noqa: E402


def _text(p: Path) -> str:
    return p.read_text(encoding="utf-8").replace("\r\n", "\n")


@pytest.mark.parametrize("gruppe,quelle,ziel", KP.KOPIEN)
def test_kopie_stimmt_mit_der_quelle_ueberein_falls_vorhanden(gruppe, quelle, ziel):
    q = KP.QUELLEN[gruppe][0] / quelle
    if not q.exists():
        pytest.skip("Quelle nicht vorhanden (CI ohne den Nachbarordner)")
    assert _text(ROOT / ziel) == KP.soll_inhalt(gruppe, quelle)


def test_rng_ist_die_vorlage_der_website_falls_vorhanden():
    if not KP.VORLAGE_RNG.exists():
        pytest.skip("Vorlage nicht vorhanden")
    assert _text(ROOT / "mek_rng.py") == _text(KP.VORLAGE_RNG)


def test_konstanten_haben_die_werte_der_quellen_falls_vorhanden():
    namen: dict = {}
    for ordner, datei in (("hyperheuristik-demo", "hhw_constants.py"), ("zugmenge-demo", "zgm_constants.py")):
        q = KP.PROJEKTE / ordner / datei
        if not q.exists():
            pytest.skip("Quelle nicht vorhanden")
        d: dict = {}
        exec(compile(_text(q), str(q), "exec"), d)
        namen.update({k: v for k, v in d.items() if k.isupper()})
    for name in C.GLEICHE_KONSTANTEN:
        assert getattr(C, name) == namen[name], name


def test_kopien_haben_kein_fremdes_praefix():
    for _, _, ziel in KP.KOPIEN:
        if ziel.endswith(".py"):
            t = _text(ROOT / ziel)
            assert "hhw_" not in t and "zgm_" not in t, ziel
