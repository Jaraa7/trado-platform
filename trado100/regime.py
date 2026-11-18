"""Market-direction regime from BTC 15m closes. ONE fixed definition, chosen before looking at results:
fast EMA (1 day) vs slow EMA (7 days) with a 0.5% dead band -> +1 up / -1 down / 0 neutral.
Used as an optional entry gate (ctx["regime"]): no new longs in -1, no new shorts in +1.
OFF in live unless the worker supplies ctx["regime"]; it does not until a backtest justifies it."""
from __future__ import annotations
import numpy as np

FAST, SLOW, BAND = 96, 672, 0.005


def _ema(x: np.ndarray, n: int) -> np.ndarray:
    a, out = 2.0 / (n + 1), np.empty(len(x))
    out[0] = x[0]
    for i in range(1, len(x)):
        out[i] = a * x[i] + (1 - a) * out[i - 1]
    return out


def regime_series(btc_bars: np.ndarray) -> np.ndarray:
    """[[ts, regime]] aligned to btc_bars; first SLOW bars are 0 (warm-up). Causal: uses closes <= ts only."""
    c = btc_bars[:, 4]
    f, s = _ema(c, FAST), _ema(c, SLOW)
    r = np.where(f > s * (1 + BAND), 1.0, np.where(f < s * (1 - BAND), -1.0, 0.0))
    r[:SLOW] = 0.0
    return np.column_stack([btc_bars[:, 0], r])


def regime_at(series: np.ndarray, ts: int) -> int:
    i = int(np.searchsorted(series[:, 0], ts, side="right")) - 1
    return int(series[i, 1]) if i >= 0 else 0


def blocks(regime: int, side: str) -> bool:
    return (regime < 0 and side == "long") or (regime > 0 and side == "short")
