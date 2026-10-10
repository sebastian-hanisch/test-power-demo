"""Jede Zahl des README (Abschnitt "Befunde") wird hier über dieselben Funktionen wie in der App nachgerechnet.

Die Messreihen sind deterministisch (SplitMix64-Pools und -Ziehungen); die Bänder sind nur Rundungs- und Plattformreserve."""

import numpy as np
import pytest

import pwr_constants as C
import pwr_evaluation as E


@pytest.fixture(scope="module")
def tables():
    return E.load_power_tables()


@pytest.fixture(scope="module")
def outcomes(pools, tables):
    out = {}
    for z, m in ((1.4, 10), (1.4, 50), (1.2, 10), (1.8, 10)):
        plans = E.pilot_plans(pools, z, m, reps=C.PILOT_REPS, relevance=C.RELEVANCE_PP)
        out[(z, m)] = (plans, E.plan_outcomes(plans, tables[z]))
    return out


def test_needed_windows_per_arm(pools, tables):
    assert E.normal_formula_n(pools, 1.4) == 26
    assert E.normal_formula_n(pools, 1.2) == 94
    assert E.normal_formula_n(pools, 1.8) == 11
    for z, expected in ((1.4, 27), (1.2, 95), (1.8, 11)):
        ns, ps = tables[z]
        assert int(ns[np.argmax(ps >= 0.8)]) == expected


def test_textbook_formula_with_equal_spread_asks_for_more_windows(pools):
    import pwr_stats as S
    sd_a = float(pools[1.0].std(ddof=1))
    assert S.n_per_arm_normal(E.true_effect(pools, 1.4), sd_a, sd_a) == 34
    assert float(pools[1.4].std(ddof=1)) < sd_a


def test_detectable_effect_shrinks_with_the_square_root_of_n(pools):
    sd_a = float(pools[1.0].std(ddof=1))
    sd_b = float(pools[1.4].std(ddof=1))
    expected = {30: 3.2, 100: 1.8, 500: 0.8}
    for n, pp in expected.items():
        assert 100 * E.detectable_effect(sd_a, sd_b, n) == pytest.approx(pp, abs=0.06)
    assert E.detectable_effect(sd_a, sd_b, 100) / E.detectable_effect(sd_a, sd_b, 400) == pytest.approx(2.0)


def test_exaggeration_by_power(pools):
    def at(z, n):
        s = E.summarize(pools, z, n, reps=C.LIVE_REPS, tag=9)
        return s["reject"], s["exaggeration"]

    p, e = at(1.4, 30)                     # etwa 86 %
    assert p == pytest.approx(0.86, abs=0.02) and e == pytest.approx(1.08, abs=0.05)
    p, e = at(1.2, 50)                     # etwa 54 %
    assert p == pytest.approx(0.54, abs=0.03) and e == pytest.approx(1.37, abs=0.08)
    p, e = at(1.2, 20)                     # etwa 26 %
    assert p == pytest.approx(0.26, abs=0.03) and e == pytest.approx(2.0, abs=0.15)
    p, e = at(1.1, 10)                     # etwa 10 %
    assert p == pytest.approx(0.10, abs=0.02) and e == pytest.approx(3.7, abs=0.4)


def test_plug_in_planning_from_a_pilot_of_ten(outcomes):
    plans, out = outcomes[(1.4, 10)]
    o = out["plugin"]
    assert o["n_median"] == pytest.approx(26, abs=2)
    assert o["n_q10"] == pytest.approx(8, abs=2) and o["n_q90"] == pytest.approx(231, abs=40)
    assert o["power_mean"] == pytest.approx(0.718, abs=0.02)
    assert o["share_below_70"] == pytest.approx(0.425, abs=0.04)


def test_planning_only_after_a_significant_pilot_is_worse(outcomes):
    plans, out = outcomes[(1.4, 10)]
    o = out["signif"]
    assert o["share_planned"] == pytest.approx(0.36, abs=0.03)
    assert o["power_mean"] == pytest.approx(0.39, abs=0.03)
    assert o["share_below_70"] == pytest.approx(1.0, abs=0.01)


def test_a_larger_pilot_helps_but_not_to_eighty_percent(outcomes):
    _, out = outcomes[(1.4, 50)]
    assert out["plugin"]["power_mean"] == pytest.approx(0.773, abs=0.02)
    assert out["plugin"]["share_below_70"] == pytest.approx(0.35, abs=0.04)


def test_relevance_and_cautious_rules(outcomes):
    _, out = outcomes[(1.4, 10)]
    assert out["relevanz"]["power_mean"] == pytest.approx(0.98, abs=0.02)
    assert out["relevanz"]["n_median"] == pytest.approx(75, abs=6)
    assert out["konserv"]["power_mean"] == pytest.approx(0.93, abs=0.02)
    assert out["konserv"]["n_median"] == pytest.approx(351, abs=45)


def test_relevance_rule_falls_short_when_the_true_effect_is_below_the_threshold(pools, outcomes):
    """Wahre Wirkung bei Faktor 1,2 ist 1,96 Punkte, knapp unter der gesetzten Schwelle von 2 Punkten."""
    assert 100 * E.true_effect(pools, 1.2) == pytest.approx(1.96, abs=0.06)
    _, out = outcomes[(1.2, 10)]
    assert out["relevanz"]["power_mean"] == pytest.approx(0.736, abs=0.03)


def test_duration_examples():
    assert E.duration_weeks(30, 10) == 48
    assert E.duration_weeks(30, 4) == 120
