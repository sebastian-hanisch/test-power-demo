"""Auswertung: Teststärke, nachweisbarer Effekt, Überschätzung und Planung aus einem Pilot (Stück 2 der Linie).

Der Pool eines Sicherheitsfaktors z ist eine große Menge unabhängiger Standort-Fenster (`generate_precomputed.py`, SplitMix64).
Ein "Experiment" zieht n Fenster je Arm mit Zurücklegen aus dem Pool; das ist für n weit unter der Poolgröße dasselbe wie n frische
Fenster, und die Wahrheit (Poolmittel) ist exakt die Wahrheit der Population, aus der gezogen wird."""

import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

import pwr_constants as C
import pwr_stats as S
from pwr_rng import uniform_block
from pwr_vehicle import run_units

PRECOMPUTED = Path(__file__).resolve().parent / "precomputed_pools.json"


@dataclass(frozen=True)
class Settings:
    z: float = C.DEFAULT_Z
    n: int = C.DEFAULT_N
    m: int = C.DEFAULT_M
    sites: int = C.DEFAULT_SITES
    seed: int = C.DEFAULT_SEED


def load_pools(path=PRECOMPUTED):
    """{z: Array der Fenster-Servicegrade}; z auf eine Nachkommastelle gerundet."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {round(float(k), 1): np.asarray(v, dtype=float) for k, v in data["pools"].items()}


def nearest_z(z):
    return min(C.Z_GRID, key=lambda g: abs(g - z))


def true_effect(pools, z_b):
    """Wahre Wirkung von Regel B gegenüber A: Mittel der Pools, B minus A (Anteil, positiv = B besser)."""
    return float(pools[nearest_z(z_b)].mean() - pools[nearest_z(C.Z_A)].mean())


def run_experiment(settings, size=None):
    """Ein Experiment mit frisch simulierten Standort-Fenstern (SplitMix64): `size` (Standard n) je Arm, Welch-Test."""
    size = settings.n if size is None else size
    a = np.asarray(run_units(C.Z_A, size, 1_000_003 * (settings.seed + 1) + 11))
    b = np.asarray(run_units(settings.z, size, 1_000_003 * (settings.seed + 1) + 977))
    return {"a": a, "b": b, "welch": S.welch(a, b)}


def run_pilot(settings):
    """Der eine Pilot der Seitenleiste: m frische Fenster je Arm, daraus die Planung der Hauptstudie."""
    res = run_experiment(settings, size=settings.m)
    w = res["welch"]
    sd_a, sd_b = float(res["a"].std(ddof=1)), float(res["b"].std(ddof=1))
    plan = float(plan_n_from_pilot(np.array([abs(w["diff"])]), np.array([sd_a]), np.array([sd_b]))[0])
    res.update({"sd_a": sd_a, "sd_b": sd_b, "plan_n": plan, "significant": w["p"] < C.ALPHA})
    return res


ROUND_WEEKS = C.WINDOW_WEEKS + C.BURN_DAYS // 7    # eine Runde: Einschwingen nach der Umstellung plus Messfenster


def duration_weeks(n_per_arm, sites):
    """Wochen, bis n Fenster je Arm (2n Fenster insgesamt) auf `sites` Standorten parallel gemessen sind."""
    rounds = -(-2 * int(n_per_arm) // int(sites))
    return rounds * ROUND_WEEKS


def load_power_tables(path=PRECOMPUTED):
    """{z: (n-Array, Teststärke-Array)} aus der vorgerechneten Messreihe."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {round(float(k), 1): (np.asarray(v["n"], dtype=float), np.asarray(v["power"], dtype=float))
            for k, v in data["power_tables"].items()}


def _indices(pool_size, count, seed):
    return np.minimum((uniform_block(seed, count) * pool_size).astype(np.int64), pool_size - 1)


def draw_experiments(pool_a, pool_b, n, reps, seed):
    """`reps` Experimente mit je n Fenstern je Arm (mit Zurücklegen aus den Pools), deterministisch aus `seed`."""
    ia = _indices(len(pool_a), reps * n, seed).reshape(reps, n)
    ib = _indices(len(pool_b), reps * n, seed + 7_919).reshape(reps, n)
    return pool_a[ia], pool_b[ib]


def experiment_seed(z, n, tag=0):
    return 5_000_000 + 10_007 * int(round(z * 10)) + 101 * n + 13 * tag


def summarize(pools, z_b, n, reps=C.LIVE_REPS, alpha=C.ALPHA, tag=0):
    """Viele Experimente bei (z_b, n): Abdeckung des 95-%-Intervalls, Entscheidungsraten, Streuung der Schätzung."""
    z_b = nearest_z(z_b)
    pool_a, pool_b = pools[nearest_z(C.Z_A)], pools[z_b]
    a, b = draw_experiments(pool_a, pool_b, n, reps, experiment_seed(z_b, n, tag))
    r = S.welch_batch(a, b, conf=1 - alpha)
    truth = true_effect(pools, z_b)
    sig = r["p"] < alpha
    covers = (r["lo"] <= truth) & (truth <= r["hi"])
    pos = sig & (r["diff"] > 0)
    neg = sig & (r["diff"] < 0)
    out = {
        "z": z_b, "n": n, "reps": reps, "truth": truth,
        "coverage": float(covers.mean()),
        "miss_low": float((r["hi"] < truth).mean()),      # Intervall komplett unter der Wahrheit
        "miss_high": float((r["lo"] > truth).mean()),     # Intervall komplett über der Wahrheit
        "reject": float(sig.mean()),
        "reject_right": float(pos.mean()),
        "reject_wrong": float(neg.mean()),
        "mean_diff": float(r["diff"].mean()),
        "sd_diff": float(r["diff"].std(ddof=1)),
        "mean_width": float((r["hi"] - r["lo"]).mean()),
        "diffs": r["diff"],
        "lo": r["lo"], "hi": r["hi"], "p": r["p"], "sig": sig, "covers": covers,
    }
    if sig.any() and truth != 0:
        out["mean_diff_sig"] = float(np.abs(r["diff"][sig]).mean())
        out["exaggeration"] = out["mean_diff_sig"] / abs(truth)
    else:
        out["mean_diff_sig"] = float("nan")
        out["exaggeration"] = float("nan")
    return out


def power_curve(pools, z_b, n_values=C.N_GRID, reps=C.LIVE_REPS):
    """Anteil signifikanter Experimente je n (Teststärke; bei z_b = 1,0 die Fehlalarmrate)."""
    return [(n, summarize(pools, z_b, n, reps)["reject"]) for n in n_values]


def normal_formula_n(pools, z_b, power=0.8):
    """Normalformel: Fenster je Arm für die gewünschte Teststärke, aus der wahren Wirkung und den Streuungen der Pools."""
    z_b = nearest_z(z_b)
    sd_a = float(pools[nearest_z(C.Z_A)].std(ddof=1))
    sd_b = float(pools[z_b].std(ddof=1))
    return S.n_per_arm_normal(true_effect(pools, z_b), sd_a, sd_b, C.ALPHA, power)


def simulated_n(pools, z_b, power=0.8, reps=C.LIVE_REPS, n_max=400):
    """Kleinstes n (Raster 1, 2, ..., 60, dann Schritte von 5), bei dem die gemessene Teststärke `power` erreicht."""
    grid = list(range(2, 61)) + list(range(65, n_max + 1, 5))
    for n in grid:
        if summarize(pools, z_b, n, reps, tag=3)["reject"] >= power:
            return n
    return None


def reduction_in_shortage(z_b):
    """Wirkung in der Sprache der Fehlmenge: Anteil der Fehlmenge, der gegenüber Regel A wegfällt (Formelwerte)."""
    import pwr_formulas as F
    a, b = F.shortage_rate(C.Z_A), F.shortage_rate(z_b)
    return a, b, 1 - b / a


# --- Stück 2: Teststärke, nachweisbarer Effekt, Planung aus einem Pilot ---------------------------------------------------

PLAN_CAP = 1000                      # größter geplanter Umfang je Arm (Fenster)
POWER_GRID = tuple(list(range(2, 61)) + list(range(65, 201, 5)) + list(range(225, PLAN_CAP + 1, 25)))


def _zsum(alpha=C.ALPHA, power=0.8):
    from scipy.special import ndtri
    return float(ndtri(1 - alpha / 2) + ndtri(power))


def power_table(pools, z_b, reps=1000, grid=POWER_GRID):
    """Gemessene Teststärke je Umfang n je Arm für den Sicherheitsfaktor z_b (bei z_b = 1,0 die Fehlalarmrate).
    Rückgabe: (n-Array, Teststärke-Array). Für n über 200 weniger Wiederholungen (Rechenzeit)."""
    ns, ps = [], []
    for n in grid:
        r = reps if n <= 200 else max(reps // 2, 300)
        ns.append(n)
        ps.append(summarize(pools, z_b, n, reps=r, tag=9)["reject"])
    return np.asarray(ns, dtype=float), np.asarray(ps, dtype=float)


def achieved_power(table, n):
    """Teststärke bei einem (auch gebrochenen oder sehr großen) Umfang n: Interpolation in der gemessenen Tabelle."""
    ns, ps = table
    return np.interp(np.clip(n, ns[0], ns[-1]), ns, ps)


def detectable_effect(sd_a, sd_b, n, alpha=C.ALPHA, power=0.8):
    """Kleinste wahre Wirkung (Anteil), die die Normalformel bei n Fenstern je Arm mit der Teststärke `power` findet."""
    return _zsum(alpha, power) * float(np.sqrt((sd_a**2 + sd_b**2) / n))


def plan_n_from_pilot(diff, sd_a, sd_b, alpha=C.ALPHA, power=0.8):
    """Normalformel mit den Schätzungen eines Pilots (Arrays); Umfang auf [2, PLAN_CAP] begrenzt, bei Wirkung 0 die Obergrenze."""
    with np.errstate(divide="ignore", invalid="ignore"):
        n = _zsum(alpha, power) ** 2 * (sd_a**2 + sd_b**2) / np.square(diff)
    n = np.where(np.isfinite(n), n, PLAN_CAP)
    return np.clip(np.ceil(n), 2, PLAN_CAP)


def pilot_plans(pools, z_b, m, reps=3000, relevance=0.02, tag=0):
    """Viele Piloten mit m Fenstern je Arm planen jeweils die Hauptstudie. Vier Planungsregeln:
    plugin (Pilot-Wirkung einsetzen), signif (nur wenn der Pilot signifikant ist), konserv (untere 80-%-Grenze der
    Pilot-Wirkung), relevanz (kleinste interessierende Wirkung `relevance`, Streuung aus dem Pilot).
    Rückgabe: dict mit geplanten Umfängen je Regel (Arrays der Länge reps; NaN = kein Plan) und die Pilot-Signifikanz."""
    z_b = nearest_z(z_b)
    pa, pb = pools[nearest_z(C.Z_A)], pools[z_b]
    a, b = draw_experiments(pa, pb, m, reps, experiment_seed(z_b, m, 100 + tag))
    r = S.welch_batch(a, b)
    diff, se = r["diff"], r["se"]
    sd_a, sd_b = a.std(axis=1, ddof=1), b.std(axis=1, ddof=1)
    sig = r["p"] < C.ALPHA
    n_plugin = plan_n_from_pilot(np.abs(diff), sd_a, sd_b)
    n_conserv = plan_n_from_pilot(np.maximum(np.abs(diff) - 1.2816 * se, 0.0), sd_a, sd_b)
    n_rel = plan_n_from_pilot(np.full(reps, relevance), sd_a, sd_b)
    return {"plugin": n_plugin, "signif": np.where(sig, n_plugin, np.nan), "konserv": n_conserv, "relevanz": n_rel,
            "pilot_sig": sig, "pilot_diff": diff}


def plan_outcomes(plans, table, power_goal=0.8):
    """Wie gut die geplanten Studien wirklich sind: erreichte Teststärke je Plan (Tabelle des wahren Sicherheitsfaktors)."""
    out = {}
    for rule in ("plugin", "signif", "konserv", "relevanz"):
        n = plans[rule]
        ok = ~np.isnan(n)
        got = achieved_power(table, n[ok])
        out[rule] = {
            "share_planned": float(ok.mean()),
            "n_median": float(np.median(n[ok])) if ok.any() else float("nan"),
            "n_q10": float(np.quantile(n[ok], 0.1)) if ok.any() else float("nan"),
            "n_q90": float(np.quantile(n[ok], 0.9)) if ok.any() else float("nan"),
            "power_mean": float(got.mean()) if ok.any() else float("nan"),
            "share_below_70": float((got < 0.7).mean()) if ok.any() else float("nan"),
            "share_reached": float((got >= power_goal - 0.02).mean()) if ok.any() else float("nan"),
        }
    return out
