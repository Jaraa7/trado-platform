"""Fast last-value indicators (numpy only, no scipy/pandas) for hot-path signal checks."""
from __future__ import annotations
import numpy as np


def ema_last(x: np.ndarray, n: int, off: int = 0) -> float:
    """EMA value `off` bars back, using a truncated (5n) exponential window."""
    end = len(x) - off
    if end <= 0:
        return float("nan")
    m = min(end, max(5 * n, 10))
    seg = x[end - m:end][::-1]
    a = 2.0 / (n + 1)
    w = (1 - a) ** np.arange(m)
    return float(np.dot(seg, w) / w.sum())


def sma_last(x: np.ndarray, n: int, off: int = 0) -> float:
    end = len(x) - off
    if end < n:
        return float("nan")
    return float(x[end - n:end].mean())


def std_last(x: np.ndarray, n: int) -> float:
    if len(x) < n:
        return float("nan")
    return float(x[-n:].std())


def rsi_last(close: np.ndarray, n: int = 14) -> float:
    if len(close) < n + 1:
        return 50.0
    d = np.diff(close[-(n + 1):])
    up = d[d > 0].sum() / n
    dn = -d[d < 0].sum() / n
    if dn == 0:
        return 100.0 if up > 0 else 50.0
    return float(100 - 100 / (1 + up / dn))


def atr_last(h: np.ndarray, l: np.ndarray, c: np.ndarray, n: int = 14) -> float:
    if len(c) < n + 1:
        return float("nan")
    hh, ll, pc = h[-n:], l[-n:], c[-n - 1:-1]
    tr = np.maximum(hh - ll, np.maximum(np.abs(hh - pc), np.abs(ll - pc)))
    return float(tr.mean())


def efficiency_ratio(close: np.ndarray, n: int) -> float:
    """Kaufman ER: 1 = clean trend, 0 = pure noise."""
    if len(close) < n + 1:
        return 0.0
    net = abs(close[-1] - close[-n - 1])
    path = np.abs(np.diff(close[-n - 1:])).sum()
    return float(net / path) if path > 0 else 0.0


def resample(candles: np.ndarray, k: int) -> np.ndarray:
    """Aggregate k consecutive bars (ts,o,h,l,c,v) -> 1 bar. Drops the incomplete tail."""
    if k <= 1:
        return candles
    n = (len(candles) // k) * k
    if n == 0:
        return candles[:0]
    c = candles[len(candles) - n:].reshape(-1, k, 6)
    out = np.empty((c.shape[0], 6))
    out[:, 0] = c[:, -1, 0]
    out[:, 1] = c[:, 0, 1]
    out[:, 2] = c[:, :, 2].max(axis=1)
    out[:, 3] = c[:, :, 3].min(axis=1)
    out[:, 4] = c[:, -1, 4]
    out[:, 5] = c[:, :, 5].sum(axis=1)
    return out
