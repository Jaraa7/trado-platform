"""Walk-forward evolution on real history (week 2).

    python -m trado100.evolve --data data/hist --gens 30 --pop 24 --workers 8

* Train period = everything except the last `--holdout-days` (default 180). Evolution NEVER sees the holdout.
* Fitness (train) = mean over K random 28-day windows of (ret - 2*maxDD - 0.15 if no trades (-0.08 if <8)) minus 0.5*std.
  Windows and symbol set are re-drawn every generation so a genome cannot memorise one stretch.
* Holdout = 6 consecutive 30-day windows. Evolved top-5 per family are compared with random genomes of
  the same family. The honest answer to "did evolution find anything?" is evolved vs random out-of-sample.
Same Manager.step() as live, so what is tested is what trades.
"""
from __future__ import annotations
import argparse, glob, json, os, random, time
from multiprocessing import Pool
from typing import Dict, List
import numpy as np

from . import genome as G
from .arena import backtest_gate
from .manager import Manager

DAY = 86_400_000
_D: dict = {}


def load(path: str) -> dict:
    hist, fund = {}, {}
    for f in sorted(glob.glob(os.path.join(path, "*USDT.npy"))):
        s = os.path.basename(f)[:-4]
        hist[s] = np.load(f)
        ff = os.path.join(path, f"{s}_funding.npy")
        fund[s] = np.load(ff) if os.path.exists(ff) else np.empty((0, 2))
    fng = os.path.join(path, "fng.npy")
    return {"hist": hist, "fund": fund, "fng": np.load(fng) if os.path.exists(fng) else np.empty((0, 2))}


def _init(path: str):
    _D.update(load(path))


def ctx_fn(sym: str, ts: int) -> dict:
    """Point-in-time funding + sentiment: last value published at or before ts (same as the worker)."""
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
    return out


def run_window(family: str, genome: dict, universe: List[str], end_ts: int, bars: int) -> dict:
    h = {s: _D["hist"][s][: int(np.searchsorted(_D["hist"][s][:, 0], end_ts, side="right"))] for s in universe}
    proto = Manager(id=0, family=family, variant=0, genome=genome, universe=universe)
    r = backtest_gate(proto, h, bars, ctx_fn)
    return {"ret": r["ret"], "dd": r["dd"], "trades": r["trades"]}


def window_score(r: dict) -> float:
    """Inactivity must never beat losing a little: no trades = -0.15, thin (<8) = -0.08."""
    pen = 0.15 if r["trades"] == 0 else (0.08 if r["trades"] < 8 else 0.0)
    return r["ret"] - 2 * r["dd"] - pen


def job(a):
    family, genome, universe, ends, bars = a
    return [run_window(family, genome, universe, e, bars) for e in ends]


def fitness(res: List[dict]) -> float:
    sc = np.array([window_score(r) for r in res])
    return float(sc.mean() - 0.5 * sc.std())


def summarize(res: List[dict]) -> dict:
    rets = [r["ret"] for r in res]
    return {"mean_ret": float(np.mean(rets)), "pos_windows": int(sum(x > 0 for x in rets)), "n_windows": len(rets),
            "worst_dd": float(max(r["dd"] for r in res)), "trades": int(sum(r["trades"] for r in res))}


def passes(s: dict) -> bool:
    return s["mean_ret"] > 0 and s["pos_windows"] * 2 >= s["n_windows"] and s["worst_dd"] < 0.12 and s["trades"] >= 40


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/hist")
    ap.add_argument("--out", default="data/evolved")
    ap.add_argument("--gens", type=int, default=30)
    ap.add_argument("--pop", type=int, default=24)
    ap.add_argument("--elite", type=int, default=4)
    ap.add_argument("--windows", type=int, default=4)
    ap.add_argument("--window-days", type=int, default=28)
    ap.add_argument("--holdout-days", type=int, default=180)
    ap.add_argument("--baseline", type=int, default=12)
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 2)
    ap.add_argument("--families", default=",".join(G.FAMILIES))
    ap.add_argument("--seed", type=int, default=11)
    a = ap.parse_args()

    rng = random.Random(a.seed)
    _init(a.data)
    syms = sorted(_D["hist"])
    assert len(syms) >= 4, f"need >=4 symbols in {a.data}"
    t0 = max(h[0][0] for h in _D["hist"].values())
    t1 = min(h[-1][0] for h in _D["hist"].values())
    hold_start = t1 - a.holdout_days * DAY
    first_end = t0 + (a.window_days + 10) * DAY
    assert hold_start > first_end, "not enough history for train + holdout"
    bars = a.window_days * 96
    fams = a.families.split(",")
    print(f"{len(syms)} symbols, {(t1 - t0) / DAY:.0f}d of data, train until holdout start "
          f"({(hold_start - t0) / DAY:.0f}d train / {a.holdout_days}d holdout)", flush=True)

    pops = {f: [G.random_genome(f, rng) for _ in range(a.pop)] for f in fams}
    t_start = time.time()
    with Pool(a.workers, initializer=_init, initargs=(a.data,)) as pool:
        for gen in range(a.gens):
            uni = rng.sample(syms, 3)
            ends = [int(rng.uniform(first_end, hold_start)) for _ in range(a.windows)]
            jobs = [(f, g, uni, ends, bars) for f in fams for g in pops[f]]
            res = pool.map(job, jobs, chunksize=1)
            k, line = 0, []
            for f in fams:
                fit = [fitness(res[k + i]) for i in range(a.pop)]
                k += a.pop
                order = sorted(range(a.pop), key=lambda i: -fit[i])
                line.append(f"{f[:5]}={fit[order[0]]:+.3f}")
                elites = [pops[f][i] for i in order[:a.elite]]
                kids = list(elites)
                while len(kids) < a.pop:
                    p1 = max(rng.sample(order[:a.pop // 2 + 1], 2), key=lambda i: fit[i])
                    p2 = max(rng.sample(order[:a.pop // 2 + 1], 2), key=lambda i: fit[i])
                    c = G.crossover(f, pops[f][p1], pops[f][p2], rng) if rng.random() < 0.5 else dict(pops[f][p1])
                    kids.append(G.mutate(f, c, rng))
                pops[f] = kids
            print(f"gen {gen + 1}/{a.gens} [{time.time() - t_start:.0f}s] best fitness: " + " ".join(line), flush=True)

        # selection on FIXED train windows, then ONE look at the holdout
        sel_ends = [int(first_end + (hold_start - first_end) * (i + 0.5) / 6) for i in range(6)]
        sel_uni = syms[:4]
        jobs = [(f, g, sel_uni, sel_ends, bars) for f in fams for g in pops[f]]
        res = pool.map(job, jobs, chunksize=1)
        top, k = {}, 0
        for f in fams:
            fit = [fitness(res[k + i]) for i in range(a.pop)]
            k += a.pop
            order = sorted(range(a.pop), key=lambda i: -fit[i])
            top[f] = [pops[f][i] for i in order[:5]]

        hold_ends = [int(hold_start + (t1 - hold_start) * (i + 1) / 6) for i in range(6)]
        hold_bars = int(a.holdout_days / 6 * 96)
        hold_uni = syms[-4:] if len(syms) >= 8 else syms[:4]
        base = {f: [G.random_genome(f, rng) for _ in range(a.baseline)] for f in fams}
        jobs = [(f, g, hold_uni, hold_ends, hold_bars) for f in fams for g in top[f] + base[f]]
        res = pool.map(job, jobs, chunksize=1)

    out, k = {}, 0
    rows = []
    for f in fams:
        ev = [summarize(res[k + i]) for i in range(len(top[f]))]
        k += len(top[f])
        bs = [summarize(res[k + i]) for i in range(len(base[f]))]
        k += len(base[f])
        out[f] = {"evolved": [{"genome": g, "oos": s, "pass": passes(s)} for g, s in zip(top[f], ev)],
                  "baseline_pass_rate": float(np.mean([passes(s) for s in bs])),
                  "baseline_median_ret": float(np.median([s["mean_ret"] for s in bs])),
                  "evolved_pass_rate": float(np.mean([passes(s) for s in ev])),
                  "evolved_median_ret": float(np.median([s["mean_ret"] for s in ev]))}
        rows.append((f, out[f]))
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "result.json"), "w") as fh:
        json.dump({"args": vars(a), "symbols": syms, "families": out}, fh, indent=1)
    lines = ["| family | evolved pass | random pass | evolved med ret/30d | random med ret/30d |", "|---|---|---|---|---|"]
    for f, o in rows:
        lines.append(f"| {f} | {o['evolved_pass_rate']:.0%} | {o['baseline_pass_rate']:.0%} | "
                     f"{o['evolved_median_ret']:+.2%} | {o['baseline_median_ret']:+.2%} |")
    rep = "\n".join(lines)
    with open(os.path.join(a.out, "report.md"), "w") as fh:
        fh.write(rep + "\n")
    print("\nOUT-OF-SAMPLE (holdout, never seen by evolution):\n" + rep, flush=True)


if __name__ == "__main__":
    main()
