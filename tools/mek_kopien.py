"""Kopien der Rundtour-Module aus den Vorgänger-Demos der Linie: welche Datei woher kommt und wie ihr Inhalt aus der Quelle entsteht.

Stück 1 (`hyperheuristik-demo`, Präfix `hhw_`) ist die Quelle des Rundtour-Kerns, Stück 2 (`zugmenge-demo`, Präfix `zgm_`) die der Auswahlregeln
und der Referenzwerte. Der Inhalt einer Kopie ist die Quelle mit ersetztem Präfix, sonst bytegleich; `tests/test_copies.py` prüft das und
überspringt sich, wenn der Nachbarordner fehlt. Fehler gehören in die Quelle, nicht in die Kopie.

Aufruf (nur beim Bau, überschreibt die Kopien):  python tools/mek_kopien.py
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJEKTE = ROOT.parent
VORLAGE_RNG = PROJEKTE / "sebastianhanisch-website" / "tools" / "templates" / "rng_splitmix64_exact.py"

QUELLEN = {
    "hhw": (PROJEKTE / "hyperheuristik-demo", "hhw_"),
    "zgm": (PROJEKTE / "zugmenge-demo", "zgm_"),
}
# (Gruppe, Datei in der Quelle, Datei hier)
KOPIEN = [
    ("hhw", "hhw_rngblock.py", "mek_rngblock.py"),
    ("hhw", "hhw_scenario.py", "mek_scenario.py"),
    ("hhw", "hhw_moves.py", "mek_moves.py"),
    ("hhw", "hhw_accept.py", "mek_accept.py"),
    ("hhw", "hhw_search.py", "mek_search.py"),
    ("zgm", "zgm_select.py", "mek_select.py"),
    ("zgm", "zgm_refs.json", "mek_refs.json"),
]


def soll_inhalt(gruppe: str, quelle: str) -> str:
    """Inhalt der Kopie, wie er aus der Quelle entsteht (Zeilenenden als \\n)."""
    ordner, alt = QUELLEN[gruppe]
    text = (ordner / quelle).read_text(encoding="utf-8").replace("\r\n", "\n")
    if quelle.endswith(".json"):
        return text
    return text.replace(alt, "mek_")


def main() -> None:
    for gruppe, quelle, ziel in KOPIEN:
        (ROOT / ziel).write_text(soll_inhalt(gruppe, quelle), encoding="utf-8", newline="\n")
        print("kopiert:", quelle, "->", ziel)
    (ROOT / "mek_rng.py").write_text(VORLAGE_RNG.read_text(encoding="utf-8").replace("\r\n", "\n"), encoding="utf-8", newline="\n")
    print("kopiert: Vorlage -> mek_rng.py")


if __name__ == "__main__":
    main()
