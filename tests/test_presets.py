"""Presets: Vollständigkeit, gültige Werte, paarweise verschieden (die zustandslose Hervorhebung braucht das), Abstand zur Voreinstellung."""

import pytest

import mek_constants as C
import mek_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.SETTING_SPECS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_allowed_values():
    for name, preset in C.PRESETS.items():
        for key, spec in P.SETTING_SPECS.items():
            if spec.options is not None:
                assert preset[key] in spec.options, (name, key)
            else:
                assert spec.lo <= preset[key] <= spec.hi, (name, key)


def test_presets_are_pairwise_different_in_at_least_two_controls():
    """Kein Preset darf nur einen Regler von der Voreinstellung (dem ersten Preset) oder von einem anderen Preset entfernt liegen:
    sonst markiert das Verschieben eines Reglers ein anderes Preset."""
    namen = list(C.PRESETS)
    for i, a in enumerate(namen):
        for b in namen[i + 1:]:
            diff = [k for k in P.SETTING_SPECS if C.PRESETS[a][k] != C.PRESETS[b][k]]
            assert len(diff) >= 2, (a, b, diff)


def test_default_preset_equals_the_spec_defaults():
    first = C.PRESETS[next(iter(C.PRESETS))]
    assert all(first[k] == spec.default for k, spec in P.SETTING_SPECS.items())


def test_url_parameters_are_unique():
    params = [s.url_param for s in P.SETTING_SPECS.values()]
    assert len(params) == len(set(params))


@pytest.mark.parametrize("key,wert,erwartet", [("rt_k", 4, 3), ("rt_k", 50, 30), ("n_inst", 3, 2), ("zeit_seed", 5000, C.SEED_MAX), ("fahrzeug", "Quatsch", "Rundtour")])
def test_einrasten(key, wert, erwartet):
    assert P._einrasten(P.SETTING_SPECS[key], wert) == erwartet


def test_wahrheitswert_des_permalinks():
    assert P._wahrheit("True") and P._wahrheit("1") and not P._wahrheit("False") and not P._wahrheit("0")
