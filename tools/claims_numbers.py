"""Gibt die Zahlen aus, die das README nennt (dieselben Funktionen wie die App); Grundlage für tests/test_claims.py."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

import pwr_constants as C  # noqa: E402
import pwr_evaluation as E  # noqa: E402

pools = E.load_pools()
tables = E.load_power_tables()
sd_a = float(pools[1.0].std(ddof=1))
print("sd_a", round(sd_a, 4))
for z in (1.2, 1.4, 1.8):
    print(f"z={z}: wahre Wirkung {100*E.true_effect(pools, z):.2f}  n80 normal {E.normal_formula_n(pools, z)}  "
          f"Tabelle 80 % ab n={int(tables[z][0][np.argmax(tables[z][1] >= 0.8)])}")
    for m in (5, 10, 20, 50):
        plans = E.pilot_plans(pools, z, m, reps=C.PILOT_REPS, relevance=C.RELEVANCE_PP)
        out = E.plan_outcomes(plans, tables[z])
        s = f"  m={m:2d} pilot_sig {100*plans['pilot_sig'].mean():5.1f} %"
        for rule in ("plugin", "signif", "konserv", "relevanz"):
            o = out[rule]
            s += (f" | {rule}: plan {100*o['share_planned']:3.0f}% n {o['n_median']:4.0f} ({o['n_q10']:4.0f}-{o['n_q90']:4.0f}) "
                  f"P {100*o['power_mean']:4.1f} <70: {100*o['share_below_70']:4.1f}")
        print(s)
print("MDE (sd_b bei z=1.4)")
sd_b = float(pools[1.4].std(ddof=1))
for n in (5, 10, 20, 30, 50, 100, 200, 500):
    print(f"  n={n}: {100*E.detectable_effect(sd_a, sd_b, n):.2f}")
print("Typ M je Teststärke (Tag 9, wie App)")
rows = []
for z in (1.1, 1.2, 1.3, 1.4, 1.6):
    for n in C.N_GRID:
        s = E.summarize(pools, z, n, reps=C.LIVE_REPS, tag=9)
        if np.isfinite(s["exaggeration"]):
            rows.append((s["reject"], s["exaggeration"], z, n))
for p, e, z, n in sorted(rows):
    print(f"  Power {100*p:5.1f} %  Faktor {e:5.2f} (z={z}, n={n})")
print("Dauer", E.duration_weeks(30, 10), E.duration_weeks(30, 4), E.duration_weeks(100, 10), E.duration_weeks(5, 60))
