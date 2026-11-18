"""Do the public-strategy candidates beat our own families? Same harness, random genomes, nothing tuned.

    python3 -u -m trado100.exp_candidates --data data/hist

Each family: N random genomes x all 30-day windows x 3 random symbols. Reported: PF, win rate, trades,
mean monthly return, and PF in the older / newer half. Bar to enter the live arena: PF > 1.3 in BOTH halves.
"""
from __future__ import annotations
import argparse, os, random
from multiprocessing import Pool

from . import candidates as C, genome as G
from .evolve import DAY
from . import exp_trend_filter as X
from .regime import SLOW

BASE = ["breakout", "regime_switch", "trend", "mean_reversion"]


def _init(path):
    C.install()
    X._init(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/hist"); ap.add_argument("--genomes", type=int, default=10)
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 2); ap.add_argument("--seed", type=int, default=11)
    a = ap.parse_args()
    _init(a.data)
    rng = random.Random(a.seed)
    syms = sorted(X._D["hist"])
    t0 = max(h[0][0] for h in X._D["hist"].values()) + (SLOW // 96 + 3) * DAY
    t1 = min(h[-1][0] for h in X._D["hist"].values())
    ends = [int(t1 - k * 30 * DAY) for k in range(int((t1 - t0) // (30 * DAY)) - 1)]
    ends = [e for e in ends if e - 30 * DAY > t0]
    mid = sorted(ends)[len(ends) // 2]
    fams = list(C.GENES) + BASE
    jobs = []
    for f in fams:
        for _ in range(a.genomes):
            g = G.random_genome(f, rng)
            for e in ends:
                jobs.append((f, g, rng.sample(syms, 3), e, False))
    with Pool(a.workers, initializer=_init, initargs=(a.data,)) as pool:
        res = pool.map(X.run, jobs, chunksize=4)
    print(f"{len(syms)} symbols, {len(ends)} windows, {a.genomes} genomes/family", flush=True)
    for f in fams:
        rows = [r for r in res if r["family"] == f]
        full, o, n = X.agg(rows), X.agg([r for r in rows if r["end"] < mid]), X.agg([r for r in rows if r["end"] >= mid])
        longs = sum(r["longs"] for r in rows)
        # best single genome by PF with >= 100 trades (optimistic upper bound, shown for context only)
        by = {}
        for r, j in zip(res, jobs):
            if r["family"] == f:
                by.setdefault(id(j[1]), []).append(r)
        best = max((X.agg(v) for v in by.values() if sum(x["n"] for x in v) >= 100), key=lambda d: d["pf"] or 0, default=None)
        tag = "candidate" if f in C.GENES else "ours"
        print(f"{f:14s} [{tag:9s}] pf {full['pf']} win {full['win_rate']} n {full['trades']:6d} long% {100 * longs // max(full['trades'], 1):3d} "
              f"ret {full['mean_ret_pct']:+.2f}%/mo dd {full['worst_dd_pct']}% | older pf {o['pf']} newer pf {n['pf']} | "
              f"best genome pf {best['pf'] if best else None} (n {best['trades'] if best else 0})", flush=True)


if __name__ == "__main__":
    main()
