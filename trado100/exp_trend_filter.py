"""Paired experiment: does the BTC direction gate (trado100/regime.py) help, out of sample-style?

    python3 -u -m trado100.exp_trend_filter --data data/hist --out data/exp_trend_filter.json

Same genome, same symbols, same 30-day windows, run twice: gate OFF vs gate ON. Nothing is tuned:
the regime definition is fixed in regime.py. Windows are non-overlapping and cover the whole history;
results are also split into older half / newer half to see whether any effect is stable.
"""
from __future__ import annotations
import argparse, json, os, random
from multiprocessing import Pool
import numpy as np

from . import genome as G
from .evolve import load, DAY
from .manager import Manager
from .regime import regime_series, regime_at, SLOW

_D: dict = {}
BARS = 30 * 96


def _init(path):
    _D.update(load(path))
    _D["reg"] = regime_series(_D["hist"]["BTCUSDT"])


def _ctx(sym, ts, gate):
    out = {}
    f = _D["fund"].get(sym)
    if f is not None and len(f):
        i = int(np.searchsorted(f[:, 0], ts, side="right")) - 1
        if i >= 0:
            out["funding"] = float(f[i, 1])
    sh = _D["fng"]
    if len(sh):
        i = int(np.searchsorted(sh[:, 0], ts, side="right")) - 1
        if i >= 0:
            out["sentiment"] = float(sh[i, 1])
    if gate:
        out["regime"] = regime_at(_D["reg"], ts)
    return out


def run(a):
    family, genome, uni, end_ts, gate = a
    m = Manager(id=-1, family=family, variant=0, genome=dict(genome), universe=list(uni))
    H = {s: _D["hist"][s] for s in uni}
    E = {s: int(np.searchsorted(H[s][:, 0], end_ts, side="right")) for s in uni}
    peak, mdd, tr = 1000.0, 0.0, []
    for j in range(BARS):
        for s in uni:
            idx = E[s] - BARS + j
            if idx < 200:
                continue
            m.step(s, H[s][max(0, idx - 3999):idx + 1], _ctx(s, int(H[s][idx][0]), gate))
        tr += m.closed; m.closed = []
        eq = m.equity(); peak = max(peak, eq); mdd = max(mdd, (peak - eq) / peak)
    m.close_all(0, "end"); tr += m.closed
    pnl = [t["pnl"] for t in tr]
    return {"family": family, "gate": gate, "end": end_ts, "ret": (m.balance - 1000) / 1000, "dd": mdd,
            "n": len(pnl), "wins": sum(p > 0 for p in pnl), "gw": sum(p for p in pnl if p > 0),
            "gl": -sum(p for p in pnl if p < 0), "longs": sum(t["side"] == "long" for t in tr)}


def agg(rows):
    n = sum(r["n"] for r in rows); gl = sum(r["gl"] for r in rows)
    return {"runs": len(rows), "mean_ret_pct": round(100 * float(np.mean([r["ret"] for r in rows])), 3),
            "trades": n, "win_rate": round(sum(r["wins"] for r in rows) / n, 3) if n else None,
            "pf": round(sum(r["gw"] for r in rows) / gl, 3) if gl else None,
            "worst_dd_pct": round(100 * max(r["dd"] for r in rows), 2)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/hist"); ap.add_argument("--out", default="data/exp_trend_filter.json")
    ap.add_argument("--genomes", type=int, default=6); ap.add_argument("--workers", type=int, default=os.cpu_count() or 2)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    _init(a.data)
    rng = random.Random(a.seed)
    syms = sorted(_D["hist"])
    t0 = max(h[0][0] for h in _D["hist"].values()) + (SLOW // 96 + 3) * DAY      # regime warm-up
    t1 = min(h[-1][0] for h in _D["hist"].values())
    ends = [int(t1 - k * 30 * DAY) for k in range(int((t1 - t0) // (30 * DAY)) - 1)]
    ends = [e for e in ends if e - 30 * DAY > t0]
    mid = sorted(ends)[len(ends) // 2]
    reg = _D["reg"][:, 1]
    print(f"{len(syms)} symbols, {len(ends)} windows of 30d; regime share: down {np.mean(reg < 0):.0%} "
          f"neutral {np.mean(reg == 0):.0%} up {np.mean(reg > 0):.0%}", flush=True)
    jobs = []
    for f in G.FAMILIES:
        for _ in range(a.genomes):
            g = G.random_genome(f, rng)
            for e in ends:
                uni = rng.sample(syms, 3)
                jobs += [(f, g, uni, e, False), (f, g, uni, e, True)]
    with Pool(a.workers, initializer=_init, initargs=(a.data,)) as pool:
        res = pool.map(run, jobs, chunksize=4)
    out = {"windows": len(ends), "genomes_per_family": a.genomes, "families": {}, "all": {}}
    for f in G.FAMILIES + ["ALL"]:
        rows = [r for r in res if f == "ALL" or r["family"] == f]
        d = {}
        for name, sel in (("full", lambda r: True), ("older_half", lambda r: r["end"] < mid), ("newer_half", lambda r: r["end"] >= mid)):
            off = [r for r in rows if not r["gate"] and sel(r)]; on = [r for r in rows if r["gate"] and sel(r)]
            better = sum(x["ret"] > y["ret"] for x, y in zip(on, off)); worse = sum(x["ret"] < y["ret"] for x, y in zip(on, off))
            d[name] = {"off": agg(off), "on": agg(on), "on_better": better, "on_worse": worse}
        out["families" if f != "ALL" else "all"][f] = d
        x = d["full"]
        print(f"{f:15s} off ret {x['off']['mean_ret_pct']:+6.2f}% pf {x['off']['pf']} win {x['off']['win_rate']} n {x['off']['trades']:5d} | "
              f"on ret {x['on']['mean_ret_pct']:+6.2f}% pf {x['on']['pf']} win {x['on']['win_rate']} n {x['on']['trades']:5d} | "
              f"better/worse {x['on_better']}/{x['on_worse']} | older {d['older_half']['on']['mean_ret_pct'] - d['older_half']['off']['mean_ret_pct']:+.2f} "
              f"newer {d['newer_half']['on']['mean_ret_pct'] - d['newer_half']['off']['mean_ret_pct']:+.2f}", flush=True)
    json.dump(out, open(a.out, "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
