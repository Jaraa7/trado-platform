"""Does open interest carry information for momentum entries? Paired, nothing tuned.

    python3 -u -m trado100.exp_oi --data data/hist

Rule fixed before looking at results: OI change over the last 24h (1h data, last value published at or
before the bar). Three runs of the same genomes/symbols/windows:
  off      - no gate
  rising   - enter only when OI rose  > +2% in 24h  ("new money confirms the move")
  falling  - enter only when OI fell  < -2% in 24h  (mirror image = the control)
If OI is informative, PF(rising) and PF(falling) must differ clearly and consistently in both halves.
"""
from __future__ import annotations
import argparse, glob, os, random
from multiprocessing import Pool
import numpy as np

from . import genome as G
from .evolve import DAY
from . import exp_trend_filter as X

FAMS = ["breakout", "trend", "regime_switch", "scalp"]
THR, LOOK = 0.02, 24
_OI: dict = {}


def _init(path):
    X._init(path)
    for f in glob.glob(os.path.join(path, "*_oi.npy")):
        a = np.load(f)
        if len(a) > LOOK:
            chg = np.full(len(a), np.nan)
            chg[LOOK:] = a[LOOK:, 1] / a[:-LOOK, 1] - 1
            _OI[os.path.basename(f)[:-7]] = np.column_stack([a[:, 0], chg])


def oi_change(sym, ts):
    a = _OI.get(sym)
    if a is None:
        return None
    i = int(np.searchsorted(a[:, 0], ts, side="right")) - 1
    return None if i < 0 or np.isnan(a[i, 1]) or ts - a[i, 0] > 3 * 3_600_000 else float(a[i, 1])


def run(a):
    family, genome, uni, end_ts, mode = a
    base = X._ctx

    def ctx(sym, ts, gate):
        out = base(sym, ts, False)
        if mode != "off":
            c = oi_change(sym, ts)
            out["skip"] = c is None or (c <= THR if mode == "rising" else c >= -THR)
        return out
    X._ctx = ctx
    try:
        r = X.run((family, genome, uni, end_ts, False))
    finally:
        X._ctx = base
    r["mode"] = mode
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/hist"); ap.add_argument("--genomes", type=int, default=8)
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 2); ap.add_argument("--seed", type=int, default=3)
    a = ap.parse_args()
    _init(a.data)
    rng = random.Random(a.seed)
    syms = sorted(s for s in X._D["hist"] if s in _OI)
    assert len(syms) >= 4, "need OI for >=4 symbols: run trado100.history_oi first"
    t0 = max(max(X._D["hist"][s][0][0], _OI[s][LOOK][0]) for s in syms) + 10 * DAY
    t1 = min(min(X._D["hist"][s][-1][0], _OI[s][-1][0]) for s in syms)
    ends = [int(t1 - k * 30 * DAY) for k in range(int((t1 - t0) // (30 * DAY)))]
    ends = [e for e in ends if e - 30 * DAY > t0]
    mid = sorted(ends)[len(ends) // 2]
    allc = np.concatenate([_OI[s][LOOK:, 1] for s in syms])
    print(f"{len(syms)} symbols with OI, {len(ends)} windows of 30d; OI 24h change: rising>{THR:.0%} in "
          f"{np.mean(allc > THR):.0%} of hours, falling<-{THR:.0%} in {np.mean(allc < -THR):.0%}", flush=True)
    jobs = []
    for f in FAMS:
        for _ in range(a.genomes):
            g = G.random_genome(f, rng)
            for e in ends:
                uni = rng.sample(syms, 3)
                jobs += [(f, g, uni, e, m) for m in ("off", "rising", "falling")]
    with Pool(a.workers, initializer=_init, initargs=(a.data,)) as pool:
        res = pool.map(run, jobs, chunksize=3)
    for f in FAMS + ["ALL"]:
        line = f"{f:14s}"
        for m in ("off", "rising", "falling"):
            rows = [r for r in res if r["mode"] == m and (f == "ALL" or r["family"] == f)]
            full = X.agg(rows); o = X.agg([r for r in rows if r["end"] < mid]); n = X.agg([r for r in rows if r["end"] >= mid])
            line += f" | {m} pf {full['pf']} win {full['win_rate']} n {full['trades']} (older {o['pf']} newer {n['pf']})"
        print(line, flush=True)


if __name__ == "__main__":
    main()
