"""Messreihe vor dem Text: Planung aus einem Pilot, nachweisbarer Effekt, Überschätzung nach Stärke (Stück 2)."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

import pwr_constants as C  # noqa: E402
import pwr_evaluation as E  # noqa: E402

pools = E.load_pools()
t0 = time.time()
print("Wahre Wirkung und Fenster je Arm für 80 % (Normalformel):")
tables = {}
for z in (1.2, 1.4, 1.8):
    tables[z] = E.power_table(pools, z)
    print(f"  z={z}: {100*E.true_effect(pools, z):.2f} Pkt.  n80 normal {E.normal_formula_n(pools, z)}  "
          f"Tabelle erreicht 80 % bei n={int(tables[z][0][np.argmax(tables[z][1] >= 0.8)])}")
print(f"(Tabellen in {time.time()-t0:.0f} s)")

print("\nPlanung aus einem Pilot: je Regel geplanter Umfang (Median, 10-90 %), erreichte Teststärke (Mittel), Anteil unter 70 %, Anteil ok")
for z in (1.2, 1.4, 1.8):
    for m in (5, 10, 20, 50):
        plans = E.pilot_plans(pools, z, m, reps=3000)
        out = E.plan_outcomes(plans, tables[z])
        print(f"z={z} m={m:2d}: Pilot signifikant {100*plans['pilot_sig'].mean():5.1f} %")
        for rule, o in out.items():
            print(f"    {rule:9s} geplant {100*o['share_planned']:5.1f} %  n {o['n_median']:6.0f} ({o['n_q10']:5.0f}-{o['n_q90']:5.0f})  "
                  f"Power {100*o['power_mean']:5.1f} %  unter 70 %: {100*o['share_below_70']:5.1f} %  ok: {100*o['share_reached']:5.1f} %")

print("\nNachweisbare Wirkung (80 %) je n, Normalformel mit sd(A) und sd(B bei z=1.4):")
sd_a = float(pools[1.0].std(ddof=1)); sd_b = float(pools[1.4].std(ddof=1))
for n in (5, 10, 20, 30, 50, 100, 200, 500):
    d = E.detectable_effect(sd_a, sd_b, n)
    print(f"  n={n:4d}: {100*d:5.2f} Pkt.")

print("\nÜberschätzung (Typ M) gegen Teststärke (Zellen z x n):")
rows = []
for z in (1.1, 1.2, 1.3, 1.4, 1.6):
    for n in (5, 10, 20, 30, 50, 100):
        s = E.summarize(pools, z, n, reps=3000)
        rows.append((s["reject"], s["exaggeration"], z, n))
rows.sort()
for p, e, z, n in rows:
    print(f"  Power {100*p:5.1f} %  Faktor {e:5.2f}   (z={z}, n={n})")
