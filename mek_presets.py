"""Permalink (Begrenzen und Einrasten), Presets und Zufalls-Seed-Button.

Alle Regler stehen in SETTING_SPECS: Zahlenregler mit Grenzen, Auswahlregler mit der Liste ihrer Werte (`options`). Die Hervorhebung des aktiven Presets ist
zustandslos und vergleicht jeden Regler mit dem Preset."""

from dataclasses import dataclass

import streamlit as st

import mek_constants as C


def _wahrheit(text) -> bool:
    return str(text).strip().lower() in ("1", "true", "ja", "wahr")


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: object
    default: object
    lo: float | None = None
    hi: float | None = None
    options: tuple | None = None


FAHRZEUGE = ("Rundtour", "Einplanung", "Bin Packing")
ZELLEN_WAHL = ("alle sechs",) + tuple(f"{f}/{n}" for f, n in C.H5_ZELLEN)
KARTE_FAHRZEUGE = ("alle",) + FAHRZEUGE
_D = C.PRESETS[next(iter(C.PRESETS))]

SETTING_SPECS = {
    "fahrzeug": SettingSpec("fz", str, _D["fahrzeug"], options=FAHRZEUGE),
    "n_inst": SettingSpec("n", int, _D["n_inst"], options=C.N_STUFEN),
    "rt_n": SettingSpec("rtn", int, _D["rt_n"], options=C.H5_NS),
    "rt_k": SettingSpec("k", int, _D["rt_k"], options=C.H5_KS),
    "rt_art": SettingSpec("art", str, _D["rt_art"], options=C.ARTEN),
    "ep_regime": SettingSpec("reg", str, _D["ep_regime"], options=C.EP_REGIME),
    "ep_b": SettingSpec("b", int, _D["ep_b"], options=C.EP_B),
    "ep_g": SettingSpec("g", int, _D["ep_g"], options=C.EP_RASTER),
    "ep_familie": SettingSpec("fam", str, _D["ep_familie"], options=C.EP_FAMILIEN),
    "bp_familie": SettingSpec("bpf", str, _D["bp_familie"], options=C.BP_FAMILIEN),
    "bp_k": SettingSpec("bpk", int, _D["bp_k"], options=C.BP_K),
    "bp_pr2": SettingSpec("pr2", int, _D["bp_pr2"], options=tuple(g * g for g in C.BP_PR2_GRID)),
    "h5_zelle": SettingSpec("zelle", str, _D["h5_zelle"], options=ZELLEN_WAHL),
    "h5_akz": SettingSpec("akz", str, _D["h5_akz"], options=C.H5_AKZ),
    "h5_stufe": SettingSpec("stufe", str, _D["h5_stufe"], options=C.STUFEN),
    "h5_r": SettingSpec("r", str, _D["h5_r"], options=C.R_STUFEN),
    "e3_fahrzeug": SettingSpec("fz3", str, _D["e3_fahrzeug"], options=("Einplanung", "Bin Packing")),
    "karte_fahrzeug": SettingSpec("kf", str, _D["karte_fahrzeug"], options=KARTE_FAHRZEUGE),
    "karte_stabil": SettingSpec("ks", _wahrheit, _D["karte_stabil"], options=(False, True)),
    "zeit_seed": SettingSpec("zs", int, _D["zeit_seed"], 0, C.SEED_MAX),
}
PRESET_KEYS = {k: k for k in SETTING_SPECS}


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def options(state_key):
    return list(SETTING_SPECS[state_key].options)


def _einrasten(spec: SettingSpec, value):
    """Wert auf die erlaubte Menge bringen: Zahlen auf die Grenzen, Auswahlwerte auf den nächsten erlaubten (Zahlen) oder den Standard (Text)."""
    if spec.options is not None:
        if value in spec.options:
            return value
        if all(isinstance(o, int) and not isinstance(o, bool) for o in spec.options) and isinstance(value, int):
            return min(spec.options, key=lambda o: (abs(o - value), o))
        return spec.default
    if spec.lo is not None:
        value = max(spec.lo, value)
    if spec.hi is not None:
        value = min(spec.hi, value)
    return value


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen, auf die erlaubten Werte begrenzt oder eingerastet."""
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                value = spec.caster(qp[spec.url_param])
            except (ValueError, TypeError):
                continue
            st.session_state[state_key] = _einrasten(spec, value)
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """`values`: {state_key: aktueller Wert}; die Adresszeile spiegelt die Konfiguration."""
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def apply_preset(name):
    for state_key in SETTING_SPECS:
        if state_key in C.PRESETS[name]:
            st.session_state[state_key] = C.PRESETS[name][state_key]


def aktives_preset():
    """Name des Presets, dessen Werte GENAU den aktuellen Einstellungen entsprechen, sonst None (zustandslos; jeder Regler aus SETTING_SPECS zählt)."""
    for name, preset in C.PRESETS.items():
        if all(st.session_state.get(state_key, spec.default) == preset.get(state_key, spec.default) for state_key, spec in SETTING_SPECS.items()):
            return name
    return None


def sidebar_presets():
    """Schnellstart oben in der Seitenleiste; das aktive Preset ist hervorgehoben (`type="primary"`)."""
    st.header("🎯 Schnellstart")
    st.caption("Ein Beispielszenario laden:")
    aktiv = aktives_preset()
    for name in C.PRESETS:
        st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}",
                  type="primary" if aktiv == name else "secondary")


def next_seed():
    """Knopf „Neuer Zufalls-Seed“: die Instanz der Zeitmessung ist der nächste Zufalls-Seed (kein random)."""
    st.session_state["zeit_seed"] = (int(st.session_state.get("zeit_seed", 0)) + 1) % (C.SEED_MAX + 1)
