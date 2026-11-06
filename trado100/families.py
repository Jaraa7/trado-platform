"""Ten signal families. Each is a pure function:
    signal(family, genome, bars, ctx) -> None | (side, stop_dist_atr_units_already_applied)
returning dict(side, stop, target) in absolute prices.

`bars` = (n,6) float array [ts,o,h,l,c,v] already resampled to the manager's timeframe.
`ctx` = optional external data: {"funding": float, "sentiment": float(-1..1), "llm": callable}.
Everything here is numpy only. Only llm_judge may call an LLM, via ctx["llm"] (>=1h bars).
"""
from __future__ import annotations
import numpy as np
from .indicators import ema_last, sma_last, std_last, rsi_last, atr_last, efficiency_ratio

MIN_BARS = 100


def _build(side: str, entry: float, atr: float, g: dict, target_override: float | None = None):
    stop_d = g["atr_stop"] * atr
    if not np.isfinite(stop_d) or stop_d <= 0 or stop_d / entry < 0.0015:
        return None
    if side == "long":
        stop = entry - stop_d
        target = entry + g["rr"] * stop_d
    else:
        stop = entry + stop_d
        target = entry - g["rr"] * stop_d
    if target_override is not None:
        # only accept a mean-reversion style target if it still pays >= 1.5R
        reward = abs(target_override - entry)
        if reward < 1.5 * stop_d or (side == "long") != (target_override > entry):
            return None
        target = target_override
    return {"side": side, "stop": stop, "target": target}


def trend(g, b, ctx):
    c = b[:, 4]
    f0, s0 = ema_last(c, g["fast"]), ema_last(c, g["slow"])
    f3, s3 = ema_last(c, g["fast"], 3), ema_last(c, g["slow"], 3)
    atr = atr_last(b[:, 2], b[:, 3], c)
    r = rsi_last(c)
    if f3 <= s3 and f0 > s0 and r > g["rsi_min"]:
        return _build("long", c[-1], atr, g)
    if f3 >= s3 and f0 < s0 and r < 100 - g["rsi_min"]:
        return _build("short", c[-1], atr, g)


def breakout(g, b, ctx):
    c, h, l, v = b[:, 4], b[:, 2], b[:, 3], b[:, 5]
    lb = g["lookback"]
    hi, lo = h[-lb - 1:-1].max(), l[-lb - 1:-1].min()
    vavg = v[-21:-1].mean()
    atr = atr_last(h, l, c)
    if v[-1] < g["vol_mult"] * vavg:
        return None
    if c[-1] > hi:
        return _build("long", c[-1], atr, g)
    if c[-1] < lo:
        return _build("short", c[-1], atr, g)


def mean_reversion(g, b, ctx):
    c = b[:, 4]
    m, sd = sma_last(c, g["bb_n"]), std_last(c, g["bb_n"])
    if not sd or not np.isfinite(sd):
        return None
    r = rsi_last(c)
    atr = atr_last(b[:, 2], b[:, 3], c)
    if c[-1] < m - g["bb_k"] * sd and r < g["rsi_lo"]:
        return _build("long", c[-1], atr, g, target_override=m)
    if c[-1] > m + g["bb_k"] * sd and r > 100 - g["rsi_lo"]:
        return _build("short", c[-1], atr, g, target_override=m)


def scalp(g, b, ctx):
    c, v = b[:, 4], b[:, 5]
    f0, s0 = ema_last(c, g["fast"]), ema_last(c, g["slow"])
    f1, s1 = ema_last(c, g["fast"], 1), ema_last(c, g["slow"], 1)
    if v[-1] < g["vol_spike"] * v[-21:-1].mean():
        return None
    atr = atr_last(b[:, 2], b[:, 3], c)
    if f1 <= s1 and f0 > s0:
        return _build("long", c[-1], atr, g)
    if f1 >= s1 and f0 < s0:
        return _build("short", c[-1], atr, g)


def grid(g, b, ctx):
    c = b[:, 4]
    m = sma_last(c, g["n"])
    atr = atr_last(b[:, 2], b[:, 3], c)
    if not atr or not np.isfinite(atr):
        return None
    z = (c[-1] - m) / atr
    if z < -g["step_atr"] * 2:
        return _build("long", c[-1], atr, g, target_override=m)
    if z > g["step_atr"] * 2:
        return _build("short", c[-1], atr, g, target_override=m)


def funding_basis(g, b, ctx):
    """Positioned against crowded funding. Needs ctx['funding'] (per-interval rate)."""
    f = ctx.get("funding")
    if f is None:
        return None
    c = b[:, 4]
    atr = atr_last(b[:, 2], b[:, 3], c)
    drift = c[-1] - ema_last(c, g["hold_ema"])
    if f > g["thr"] and drift < 0:      # longs crowded, price already rolling over
        return _build("short", c[-1], atr, g)
    if f < -g["thr"] and drift > 0:
        return _build("long", c[-1], atr, g)


def regime_switch(g, b, ctx):
    c = b[:, 4]
    er = efficiency_ratio(c, g["er_n"])
    atr = atr_last(b[:, 2], b[:, 3], c)
    if er >= g["er_thr"]:  # trending -> follow
        f, s = ema_last(c, g["fast"]), ema_last(c, g["slow"])
        if f > s and c[-1] > f:
            return _build("long", c[-1], atr, g)
        if f < s and c[-1] < f:
            return _build("short", c[-1], atr, g)
    else:                  # ranging -> fade
        m, sd = sma_last(c, 20), std_last(c, 20)
        if sd and c[-1] < m - 2 * sd:
            return _build("long", c[-1], atr, g, target_override=m)
        if sd and c[-1] > m + 2 * sd:
            return _build("short", c[-1], atr, g, target_override=m)


def sentiment(g, b, ctx):
    """Contrarian at extremes, confirmed by price turning. Needs ctx['sentiment'] in [-1,1]."""
    s = ctx.get("sentiment")
    if s is None:
        return None
    c = b[:, 4]
    atr = atr_last(b[:, 2], b[:, 3], c)
    turn = c[-1] - c[-g["confirm_n"]]
    if s <= -g["extreme"] and turn > 0:
        return _build("long", c[-1], atr, g)
    if s >= g["extreme"] and turn < 0:
        return _build("short", c[-1], atr, g)


def accumulate(g, b, ctx):
    """Long-only dip buyer with a wide stop."""
    c = b[:, 4]
    m = sma_last(c, g["n"])
    atr = atr_last(b[:, 2], b[:, 3], c)
    if c[-1] < m * (1 - g["dip_pct"]) and rsi_last(c) < 40:
        return _build("long", c[-1], atr, g)


def llm_judge(g, b, ctx):
    """>=1h bars only. If ctx['llm'] is wired, it decides; otherwise a rule-vote fallback
    (no LLM cost) so the seat still trades until the LLM client is attached."""
    judge = ctx.get("llm")
    c = b[:, 4]
    atr = atr_last(b[:, 2], b[:, 3], c)
    if judge is not None:
        side = judge(c[-60:], ctx)
        return _build(side, c[-1], atr, g) if side in ("long", "short") else None
    votes = 0
    for fn, gg in ((trend, {**g, "fast": 12, "slow": 48, "rsi_min": 50}),
                   (breakout, {**g, "lookback": 30, "vol_mult": 1.0}),
                   (mean_reversion, {**g, "bb_n": 20, "bb_k": 2.0, "rsi_lo": 30})):
        s = fn(gg, b, ctx)
        if s:
            votes += 1 if s["side"] == "long" else -1
    if votes >= g["votes_needed"] - 1 and votes > 0:
        return _build("long", c[-1], atr, g)
    if -votes >= g["votes_needed"] - 1 and votes < 0:
        return _build("short", c[-1], atr, g)


REGISTRY = {
    "trend": trend, "breakout": breakout, "mean_reversion": mean_reversion, "scalp": scalp,
    "grid": grid, "funding_basis": funding_basis, "regime_switch": regime_switch,
    "sentiment": sentiment, "accumulate": accumulate, "llm_judge": llm_judge,
}


def signal(family: str, genome: dict, bars: np.ndarray, ctx: dict | None = None):
    if len(bars) < MIN_BARS:
        return None
    try:
        return REGISTRY[family](genome, bars, ctx or {})
    except (ValueError, FloatingPointError, ZeroDivisionError):
        return None
