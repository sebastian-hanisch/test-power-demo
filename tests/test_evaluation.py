"""Auswertung: Experimente aus dem Pool, Wahrheit, Teststärke, Normalformel."""

import numpy as np
import pytest

import pwr_constants as C
import pwr_evaluation as E


def test_pools_are_complete_and_inside_the_unit_interval(pools):
    assert sorted(pools) == list(C.Z_GRID)
    for z, values in pools.items():
        assert len(values) == C.POOL_SIZE
        assert values.min() >= 0.0 and values.max() <= 1.0


def test_pool_truth_is_zero_without_effect_and_grows_with_z(pools):
    assert E.true_effect(pools, 1.0) == 0.0
    effects = [E.true_effect(pools, z) for z in C.Z_GRID[1:]]
    assert all(b > a for a, b in zip(effects, effects[1:]))
    assert effects[0] > 0.01


def test_nearest_z_snaps_to_the_grid():
    assert E.nearest_z(1.43) == 1.4
    assert E.nearest_z(2.7) == 2.0
    assert E.nearest_z(0.2) == 1.0


def test_run_experiment_is_deterministic_and_seed_dependent():
    s = E.Settings(z=1.4, n=10, seed=5)
    a, b = E.run_experiment(s), E.run_experiment(s)
    assert np.array_equal(a["a"], b["a"]) and np.array_equal(a["b"], b["b"])
    c = E.run_experiment(E.Settings(z=1.4, n=10, seed=6))
    assert not np.array_equal(a["a"], c["a"])
    assert len(a["a"]) == len(a["b"]) == 10


def test_draw_experiments_has_the_requested_shape_and_comes_from_the_pool(pools):
    a, b = E.draw_experiments(pools[1.0], pools[1.4], n=7, reps=50, seed=3)
    assert a.shape == b.shape == (50, 7)
    assert set(np.unique(a)) <= set(np.unique(pools[1.0]))
    a2, _ = E.draw_experiments(pools[1.0], pools[1.4], n=7, reps=50, seed=3)
    assert np.array_equal(a, a2)


def test_interval_coverage_is_close_to_95_percent(pools):
    for z, n in ((1.4, 30), (1.2, 10), (1.8, 100)):
        s = E.summarize(pools, z, n, reps=3000)
        assert 0.925 < s["coverage"] < 0.975, (z, n, s["coverage"])


def test_false_alarm_rate_without_effect_is_close_to_five_percent(pools):
    for n in (10, 30, 100):
        s = E.summarize(pools, 1.0, n, reps=3000)
        assert 0.03 < s["reject"] < 0.07, (n, s["reject"])


def test_power_grows_with_the_number_of_windows_and_with_the_effect(pools):
    low_n = E.summarize(pools, 1.4, 10, reps=2000)["reject"]
    high_n = E.summarize(pools, 1.4, 50, reps=2000)["reject"]
    assert high_n > low_n + 0.3
    small = E.summarize(pools, 1.2, 30, reps=2000)["reject"]
    large = E.summarize(pools, 1.8, 30, reps=2000)["reject"]
    assert large > small + 0.3


def test_exaggeration_is_large_when_power_is_low(pools):
    s = E.summarize(pools, 1.2, 5, reps=3000)
    assert s["reject"] < 0.15
    assert s["exaggeration"] > 2.0
    s_big = E.summarize(pools, 1.8, 100, reps=2000)
    assert s_big["exaggeration"] == pytest.approx(1.0, abs=0.03)


def test_normal_formula_agrees_with_the_simulated_sample_size(pools):
    for z in (1.2, 1.4, 1.8):
        normal = E.normal_formula_n(pools, z)
        sim = E.simulated_n(pools, z, reps=2000)
        assert sim is not None
        assert abs(sim - normal) <= max(3, 0.15 * normal), (z, normal, sim)


def test_shortage_reduction_by_hand_form():
    a, b, red = E.reduction_in_shortage(1.4)
    assert a > b > 0
    assert red == pytest.approx(1 - b / a)
    assert 0.3 < red < 0.7
