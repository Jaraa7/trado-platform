"""Paired experiment: funding_basis with the current funding threshold vs a 4x lower one.

    python3 -u -m trado100.exp_funding_thr --data data/hist

Live thresholds (0.02%..0.12% per 8h) sit far above normal funding (median ~0.005%), so the family
almost never trades. Same genomes/symbols/30-day windows, only `thr` differs. Judge by PF and win rate.
"""
from __future__ import annotations
import argparse, os, random
from multiprocessing import Pool

from . import genome as G
from .evolve import DAY
from .exp_trend_filter import _D, _init, run, agg
from .regime import SLOW


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/hist"); ap.add_argument("--genomes", type=int, default=12)
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 2); ap.add_argument("--seed", type=int, default=5)
    a = ap.parse_args()
    _init(a.data)
    rng = random.Random(a.seed)
    syms = sorted(_D["hist"])
    t0 = max(h[0][0] for h in _D["hist"].values()) + (SLOW // 96 + 3) * DAY
    t1 = min(h[-1][0] for h in _D["hist"].values())
    ends = [int(t1 - k * 30 * DAY) for k in range(int((t1 - t0) // (30 * DAY)) - 1)]
    ends = [e for e in ends if e - 30 * DAY > t0]
    mid = sorted(ends)[len(ends) // 2]
    jobs, tag = [], []
    for _ in range(a.genomes):
        g = G.random_genome("funding_basis", rng)
        for e in ends:
            uni = rng.sample(syms, 3)
            for name, div in (("current", 1), ("div4", 4), ("div10", 10)):
                jobs.append(("funding_basis", dict(g, thr=g["thr"] / div), uni, e, False)); tag.append(name)
    with Pool(a.workers, initializer=_init, initargs=(a.data,)) as pool:
        res = pool.map(run, jobs, chunksize=4)
    for name in ("current", "div4", "div10"):
        rows = [r for r, t in zip(res, tag) if t == name]
        full, old, new = agg(rows), agg([r for r in rows if r["end"] < mid]), agg([r for r in rows if r["end"] >= mid])
        print(f"{name:8s} ret {full['mean_ret_pct']:+.2f}% pf {full['pf']} win {full['win_rate']} n {full['trades']} dd {full['worst_dd_pct']}% | "
              f"older pf {old['pf']} n {old['trades']} | newer pf {new['pf']} n {new['trades']}", flush=True)


if __name__ == "__main__":
    main()
