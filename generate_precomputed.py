"""Erzeugt `precomputed_pools.json`: je Sicherheitsfaktor (1) eine große Menge unabhängiger Standort-Fenster (Servicegrad) und
(2) die gemessene Teststärke je Umfang (Tabelle für die Planung aus einem Pilot).

    python generate_precomputed.py            # einige Minuten, nutzt alle Kerne

Jede Einheit ist ein eigener SplitMix64-Strom mit festem Seed (Z-Index, Einheit); die Teststärke-Tabellen ziehen aus den Pools mit
SplitMix64-Indizes: das Ergebnis hängt weder von der Zahl der Prozesse noch von der Plattform ab."""

import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

import numpy as np

import pwr_constants as C
from pwr_rng import SplitMix64
from pwr_vehicle import window_service_level

OUT = Path(__file__).resolve().parent / "precomputed_pools.json"
_POOLS = None


def unit_seed(z_index, i):
    return 9_000_011 * (z_index + 1) + 7 * i + 1


def _chunk(args):
    z_index, z, start, stop = args
    return [round(window_service_level(z, SplitMix64(unit_seed(z_index, i))), 6) for i in range(start, stop)]


def _init(pools):
    global _POOLS
    _POOLS = pools


def _table(z):
    import pwr_evaluation as E
    ns, ps = E.power_table(_POOLS, z)
    return z, [int(n) for n in ns], [round(float(p), 4) for p in ps]


def main():
    t0 = time.time()
    step = 500
    jobs = [(zi, z, s, min(s + step, C.POOL_SIZE)) for zi, z in enumerate(C.Z_GRID) for s in range(0, C.POOL_SIZE, step)]
    with mp.Pool() as pool:
        parts = pool.map(_chunk, jobs)
    pools = {f"{z:.1f}": [] for z in C.Z_GRID}
    for (zi, z, _s, _e), values in zip(jobs, parts):
        pools[f"{z:.1f}"].extend(values)
    arrays = {round(float(k), 1): np.asarray(v, dtype=float) for k, v in pools.items()}
    with mp.Pool(initializer=_init, initargs=(arrays,)) as pool:
        tables = pool.map(_table, list(C.Z_GRID))
    meta = {"pool_size": C.POOL_SIZE, "window_days": C.WINDOW_DAYS, "burn_days": C.BURN_DAYS, "base_mean": C.BASE_MEAN,
            "disp": C.DISP, "lead": C.LEAD, "z_grid": list(C.Z_GRID)}
    power_tables = {f"{z:.1f}": {"n": ns, "power": ps} for z, ns, ps in tables}
    OUT.write_text(json.dumps({"meta": meta, "pools": pools, "power_tables": power_tables}, separators=(",", ":")),
                   encoding="utf-8")
    print(f"{OUT.name}: {len(C.Z_GRID)} Pools à {C.POOL_SIZE} Fenster, {len(tables)} Teststärke-Tabellen, "
          f"{time.time() - t0:.0f} s, {OUT.stat().st_size / 1024:.0f} KB", file=sys.stderr)


if __name__ == "__main__":
    main()
