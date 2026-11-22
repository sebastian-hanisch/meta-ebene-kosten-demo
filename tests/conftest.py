"""Gemeinsame Einrichtung: Projektordner und tools/ auf den Importpfad (Mini-Instanzen stehen in den Testdateien, je Einheit von Hand gerechnet)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
