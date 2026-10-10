"""Planung, nachweisbarer Effekt, Dauer, Teststärke-Tabelle: Handrechnung und Konsistenz."""

import numpy as np
import pytest

import pwr_constants as C
import pwr_evaluation as E


def test_plan_n_from_pilot_by_hand():
    # (1,95996 + 0,84162)^2 = 7,8489; Wirkung 0,05, beide Streuungen 0,05: 7,8489 * 0,005 / 0,0025 = 15,70 -> 16
    n = E.plan_n_from_pilot(np.array([0.05]), np.array([0.05]), np.array([0.05]))
    assert n[0] == 16


def test_plan_n_is_clipped_to_the_allowed_range():
    n = E.plan_n_from_pilot(np.array([0.0, 1e-9, 5.0]), np.array([0.05] * 3), np.array([0.05] * 3))
    assert n[0] == E.PLAN_CAP and n[1] == E.PLAN_CAP and n[2] == 2


def test_detectable_effect_by_hand_and_the_square_root_law():
    # 2,8016 * sqrt((0,05^2 + 0,05^2) / 50) = 2,8016 * 0,01 = 0,028016
    assert E.detectable_effect(0.05, 0.05, 50) == pytest.approx(0.028016, abs=2e-5)
    # vierfacher Umfang, halbe nachweisbare Wirkung
    assert E.detectable_effect(0.05, 0.05, 200) == pytest.approx(E.detectable_effect(0.05, 0.05, 50) / 2)


def test_duration_in_weeks():
    assert E.ROUND_WEEKS == 8
    assert E.duration_weeks(30, 10) == 48          # 60 Fenster / 10 Standorte = 6 Runden zu 8 Wochen
    assert E.duration_weeks(30, 4) == 120          # 15 Runden
    assert E.duration_weeks(5, 60) == 8            # eine Runde


def test_achieved_power_interpolates_and_clips():
    table = (np.array([2.0, 10.0]), np.array([0.1, 0.5]))
    assert E.achieved_power(table, 6) == pytest.approx(0.3)
    assert E.achieved_power(table, 1) == pytest.approx(0.1)
    assert E.achieved_power(table, 100) == pytest.approx(0.5)


def test_power_tables_are_complete_and_grow_with_n():
    tables = E.load_power_tables()
    assert sorted(tables) == list(C.Z_GRID)
    ns, ps = tables[1.4]
    assert list(ns) == [float(n) for n in E.POWER_GRID]
    assert ps[ns == 5][0] < ps[ns == 30][0] < ps[ns == 100][0]
    assert ps[ns == 1000][0] > 0.99
    # ohne Wirkung ist die Kurve die Fehlalarmrate
    ns0, ps0 = tables[1.0]
    assert np.all((ps0 > 0.0) & (ps0 < 0.12))


def test_the_table_equals_the_live_measurement_with_the_same_draw(pools):
    tables = E.load_power_tables()
    ns, ps = tables[1.4]
    live = E.summarize(pools, 1.4, 30, reps=1000, tag=9)["reject"]
    assert ps[ns == 30][0] == pytest.approx(live, abs=1e-4)


def test_pilot_plans_shapes_and_rules(pools):
    plans = E.pilot_plans(pools, 1.4, 10, reps=300)
    for rule in ("plugin", "signif", "konserv", "relevanz"):
        assert plans[rule].shape == (300,)
    sig = plans["pilot_sig"]
    assert np.all(np.isnan(plans["signif"][~sig])) and not np.any(np.isnan(plans["signif"][sig]))
    assert np.all(plans["plugin"][sig] == plans["signif"][sig])
    assert np.nanmin(plans["konserv"]) >= np.nanmin(plans["plugin"])
    assert np.all(plans["konserv"] >= plans["plugin"])         # untere Grenze: nie kleiner als die Punktschätzung


def test_relevance_rule_ignores_the_pilot_effect(pools):
    a = E.pilot_plans(pools, 1.2, 20, reps=300, relevance=0.02)["relevanz"]
    b = E.pilot_plans(pools, 1.8, 20, reps=300, relevance=0.02)["relevanz"]
    # gleiche Pilotgröße, andere Wahrheit: nur die Streuung der Pilote geht ein, der Umfang liegt in derselben Größenordnung
    assert 0.5 < np.median(a) / np.median(b) < 2.0


def test_run_pilot_is_deterministic_and_plan_is_in_range():
    s = E.Settings(1.4, 30, 10, 10, 5)
    p1, p2 = E.run_pilot(s), E.run_pilot(s)
    assert np.array_equal(p1["a"], p2["a"]) and p1["plan_n"] == p2["plan_n"]
    assert len(p1["a"]) == 10
    assert 2 <= p1["plan_n"] <= E.PLAN_CAP


def test_plan_outcomes_shares_are_consistent(pools):
    tables = E.load_power_tables()
    plans = E.pilot_plans(pools, 1.4, 10, reps=400)
    out = E.plan_outcomes(plans, tables[1.4])
    assert out["plugin"]["share_planned"] == 1.0
    assert out["signif"]["share_planned"] == pytest.approx(float(plans["pilot_sig"].mean()))
    for o in out.values():
        if o["share_planned"] > 0:
            assert 0.0 <= o["power_mean"] <= 1.0 and 0.0 <= o["share_below_70"] <= 1.0
