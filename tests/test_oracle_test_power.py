"""Orakel-Tests: der Kern gegen einen unabhängigen Rechenweg (ORACLE-PLAYBOOK §2).

1. Servicegrad: die geschlossene Formel (Summen negativ-binomialer Verteilungen) gegen die Faltung der Ein-Tages-Verteilung
   und gegen die Simulation des Vehikels.
2. Welch-Test: gegen scipy.stats.ttest_ind und gegen die Abdeckung auf Normaldaten (95 % exakt).
3. Wahrheit der Pools gegen die Formel."""

import numpy as np
import pytest
from scipy import stats

import pwr_constants as C
import pwr_formulas as F
import pwr_stats as S
import pwr_vehicle as V
from pwr_rng import SplitMix64


def _convolved_fill_rate(z):
    """Unabhängiger Weg: Verteilung der Nachfrage von L Tagen durch Faltung der Ein-Tages-Verteilung (statt NegBin-Summe)."""
    size, mean = C.DISP, C.BASE_MEAN
    kmax = 400
    day = stats.nbinom.pmf(np.arange(kmax), size, size / (size + mean))
    level = V.order_up_to_level(z)

    def excess(n_days):
        dist = np.array([1.0])
        for _ in range(n_days):
            dist = np.convolve(dist, day)[:kmax]
        k = np.arange(len(dist))
        return float((np.maximum(k - level, 0) * dist).sum())

    return 1.0 - (excess(C.LEAD) - excess(C.LEAD - 1)) / mean


@pytest.mark.parametrize("z", [1.0, 1.4, 2.0])
def test_fill_rate_formula_equals_the_convolution(z):
    assert F.fill_rate(z) == pytest.approx(_convolved_fill_rate(z), abs=2e-5)


def test_fill_rate_increases_with_the_safety_factor():
    rates = [F.fill_rate(z) for z in C.Z_GRID]
    assert all(b > a for a, b in zip(rates, rates[1:]))
    assert 0.9 < rates[0] < 0.95 and rates[-1] > 0.98


@pytest.mark.parametrize("z", [1.0, 1.4])
def test_simulated_service_level_matches_the_formula(z):
    """Quote der Summen über viele Fenster gegen die exakte Formel; Standardfehler etwa 0,0008."""
    rng = SplitMix64(31 + int(10 * z))
    demand = short = 0
    for _ in range(1200):
        d, s = V.simulate_window(z, rng)
        demand += d
        short += s
    assert 1 - short / demand == pytest.approx(F.fill_rate(z), abs=0.004)


def test_pool_means_are_close_to_the_formula(pools):
    """Mittel der Fenster-Quoten liegt wegen der Mittelung von Quoten (statt Quote der Summen) geringfügig darüber."""
    for z in (1.0, 1.4, 2.0):
        assert pools[z].mean() == pytest.approx(F.fill_rate(z), abs=0.004)


def test_welch_interval_covers_with_95_percent_on_normal_data():
    rng = np.random.default_rng(11)
    reps, n = 6000, 12
    a = rng.normal(0.0, 1.0, (reps, n))
    b = rng.normal(0.4, 2.5, (reps, n))
    r = S.welch_batch(a, b)
    coverage = float(((r["lo"] <= 0.4) & (0.4 <= r["hi"])).mean())
    assert coverage == pytest.approx(0.95, abs=0.012)


def test_welch_false_alarm_rate_on_normal_data_is_five_percent():
    rng = np.random.default_rng(12)
    r = S.welch_batch(rng.normal(0, 1, (6000, 15)), rng.normal(0, 3, (6000, 8)))
    assert float((r["p"] < 0.05).mean()) == pytest.approx(0.05, abs=0.012)
