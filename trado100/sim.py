"""Offline simulation: python -m trado100.sim [--days 30]. Proves the mechanics end-to-end."""
from __future__ import annotations
import argparse, random, time
import numpy as np
from .arena import Arena
from .store import InMemoryStore
from .synth import make_world, ctx_factory, BAR


def run(days=30, symbols=8, warm=1500, gate=800, seed=7, per_family=10, verbose=True):
    syms = [f"S{k}USDT" for k in range(symbols)]
    n_total = warm + days * 96
    world = make_world(syms, n_total, seed)
    ctx_fn = ctx_factory(world)
    view = {s: world[s][:warm] for s in syms}
    st = InMemoryStore()
    arena = Arena(st, view, random.Random(seed), gate_bars=gate, ctx_fn=ctx_fn, size_per_family=per_family)
    t0 = time.time()
    ts0 = int(world[syms[0]][warm - 1][0])
    arena.seed(ts0)
    if verbose:
        print(f"seeded {len(arena.managers)} managers, vacancies={len(arena.vacancies)} in {time.time()-t0:.0f}s")
    t1 = time.time()
    for i in range(warm, n_total):
        for s in syms:
            view[s] = world[s][:i + 1]
        ts = int(world[syms[0]][i][0])
        for s in syms:
            arena.feed(s, ctx_fn(s, ts))
        arena.end_step(ts)
        if (ts // (7 * 86_400_000)) != ((ts - BAR) // (7 * 86_400_000)):
            arena.weekly_postmortem(ts)
    for m in arena.managers.values():
        arena.flush_trades(m)
    if verbose:
        print(f"simulated {days}d x {symbols} symbols in {time.time()-t1:.0f}s")
    return arena, st


def report(arena, st):
    alive = [m for m in arena.managers.values() if m.status != "dead"]
    print(f"alive={len(alive)} dead={len(st.deaths)} trades={len(st.trades)} vacancies={len(arena.vacancies)}")
    print("seats:", arena.seats())
    from collections import Counter
    print("death causes:", dict(Counter(d['cause'] for d in st.deaths)))
    eq = sorted(((m.equity(), m.family, m.generation) for m in alive), reverse=True)
    print("top3:", [(round(e), f, g) for e, f, g in eq[:3]], "worst3:", [(round(e), f, g) for e, f, g in eq[-3:]])
    tot = sum(m.equity() for m in alive) / (1000 * len(alive)) - 1
    print(f"avg alive return: {tot:+.2%}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    a = ap.parse_args()
    report(*run(a.days))
