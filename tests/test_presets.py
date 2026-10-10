"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, Einrasten der Permalink-Werte."""

import pwr_constants as C
import pwr_evaluation as ev
import pwr_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP) == set(C.PRESET_ORDER)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds_and_on_the_grid():
    for preset in C.PRESETS.values():
        assert C.Z_MIN <= preset["z"] <= C.Z_MAX and preset["z"] in C.Z_GRID
        assert C.N_MIN <= preset["n"] <= C.N_MAX and (preset["n"] - C.N_MIN) % C.N_STEP == 0
        assert C.M_MIN <= preset["m"] <= C.M_MAX and (preset["m"] - C.M_MIN) % C.M_STEP == 0
        assert C.SITES_MIN <= preset["sites"] <= C.SITES_MAX and (preset["sites"] - C.SITES_MIN) % C.SITES_STEP == 0
        assert 0 <= preset["seed"] <= C.SEED_MAX


def test_default_preset_equals_the_default_settings():
    first = C.PRESET_ORDER[0]
    assert ev.Settings(**C.PRESETS[first]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_permalink_values_are_clamped_and_snapped_to_the_slider_grid():
    z_spec = P.SETTING_SPECS["z_slider"]
    assert P.clamp_to_spec(z_spec, 1.47) == 1.5
    assert P.clamp_to_spec(z_spec, 9.0) == 2.0
    assert P.clamp_to_spec(z_spec, -3.0) == 1.0
    n_spec = P.SETTING_SPECS["n_slider"]
    assert P.clamp_to_spec(n_spec, 33) == 35
    assert P.clamp_to_spec(n_spec, 1) == 5
    assert P.clamp_to_spec(n_spec, 10_000) == 200
    m_spec = P.SETTING_SPECS["m_slider"]
    assert P.clamp_to_spec(m_spec, 12) == 10 and P.clamp_to_spec(m_spec, 500) == 100
    sites_spec = P.SETTING_SPECS["sites_slider"]
    assert P.clamp_to_spec(sites_spec, 10) == 10 and P.clamp_to_spec(sites_spec, 1) == 4
    assert P.clamp_to_spec(sites_spec, 9) in (8, 10)       # genau zwischen zwei Rasterwerten
    seed_spec = P.SETTING_SPECS["seed_input"]
    assert P.clamp_to_spec(seed_spec, 123) == 123


def test_z_grid_has_eleven_values_from_one_to_two():
    assert C.Z_GRID[0] == 1.0 and C.Z_GRID[-1] == 2.0 and len(C.Z_GRID) == 11
