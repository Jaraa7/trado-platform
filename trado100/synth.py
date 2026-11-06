"""Synthetic 15m market generator (regime-switching GBM) — for tests/sim only.
No real edge exists in this data by construction; it validates mechanics, not profitability."""
from __future__ import annotations
import numpy as np

BAR = 900_000


def make_bars(n: int, seed: int, start_ts: int = 1_760_000_000_000, p0: float = 100.0) -> np.ndarray:
    r = np.random.default_rng(seed)
    out = np.empty((n, 6))
    price, ts = p0, start_ts - start_ts % BAR
    regime, left = 0, 0
    drift, vol = 0.0, 0.003
    for i in range(n):
        if left <= 0:
            regime = r.integers(0, 3)                  # 0 range, 1 up, 2 down
            drift = [0.0, 0.0006, -0.0006][regime]
            vol = r.uniform(0.002, 0.006)
            left = int(r.integers(80, 400))
        left -= 1
        ret = drift + vol * r.standard_normal()
        if regime == 0:                                 # mean reverting in range
            ret -= 0.05 * (price - p0) / p0 * 0.1
        o = price
        c = o * (1 + ret)
        hi = max(o, c) * (1 + abs(r.standard_normal()) * vol * 0.5)
        lo = min(o, c) * (1 - abs(r.standard_normal()) * vol * 0.5)
        v = 1000 * (1 + 40 * abs(ret) / max(vol, 1e-6) * 0.1 + abs(r.standard_normal()) * 0.3)
        out[i] = (ts, o, hi, lo, c, v)
        price, ts = c, ts + BAR
    return out


def make_world(symbols, n, seed=1):
    return {s: make_bars(n, seed * 1000 + k, p0=50 + 20 * k) for k, s in enumerate(symbols)}


def ctx_factory(world):
    """funding ~ trailing return (crowded longs after pumps); sentiment ~ slow trailing return."""
    def fn(sym, ts):
        a = world[sym]
        i = int((ts - a[0][0]) // BAR)
        if i < 100:
            return {}
        c = a[:, 4]
        tr = c[i] / c[i - 96] - 1
        sl = c[i] / c[i - 96 * 3 if i >= 288 else 0] - 1
        return {"funding": float(np.clip(tr * 0.02, -0.003, 0.003)),
                "sentiment": float(np.clip(sl * 6, -1, 1))}
    return fn
