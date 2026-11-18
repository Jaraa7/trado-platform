"""Candidate families inspired by well-known public Freqtrade strategies. RESEARCH ONLY.

Not part of the live system: nothing here is registered unless install() is called (only the
experiment calls it), and genome.FAMILIES (the live seat list) is never changed.

These are re-implementations of the *entry ideas*, adapted to our rules (ATR stop, R:R >= 1.5 target,
long AND short mirror, risk <= 2%). They are not copies of the originals, which use ROI tables,
-10%..-35% stops and re-buys that the Risk Guardian would refuse.

  ewo_dip     - "SMAOffset + Elliott Wave Oscillator" (NostalgiaForInfinity lineage): buy a dip below
                a moving average only while the fast/slow EMA momentum (EWO) is still strongly up.
  supertrend  - classic ATR-band trend flip (many public Supertrend strategies).
  cluc        - "ClucMay72018" (freqtrade-strategies): close well below the lower Bollinger band,
                below the slow EMA, on quiet volume; exit at the band middle.
"""
from __future__ import annotations
import numpy as np
from . import families as F, genome as G
from .indicators import ema_last, sma_last, std_last, rsi_last, atr_last

GENES = {
    "ewo_dip":    {"base_n": (14, 50, True), "off": (0.01, 0.045, False), "ewo": (0.5, 4.0, False), "rsi_buy": (35, 60, False)},
    "supertrend": {"st_n": (7, 21, True), "st_mult": (1.5, 4.5, False)},
    "cluc":       {"bb_n": (20, 40, True), "below": (0.003, 0.02, False), "vol_q": (0.6, 1.5, False)},
}


def ewo_dip(g, b, ctx):
    c = b[:, 4]
    base = ema_last(c, g["base_n"])
    ewo = (ema_last(c, 50) - ema_last(c, 200)) / c[-1] * 100      # as in SMAOffset: EMA50 vs EMA200
    r = rsi_last(c)
    atr = atr_last(b[:, 2], b[:, 3], c)
    if c[-1] < base * (1 - g["off"]) and ewo > g["ewo"] and r < g["rsi_buy"]:
        return F._build("long", c[-1], atr, g)
    if c[-1] > base * (1 + g["off"]) and ewo < -g["ewo"] and r > 100 - g["rsi_buy"]:
        return F._build("short", c[-1], atr, g)


def _st_dir(h, l, c, n, mult):
    """Supertrend direction (+1/-1) for the last two bars, computed over a causal 6n window."""
    m = min(len(c) - 1, 6 * n + 2)
    h, l, c = h[-m - 1:], l[-m - 1:], c[-m - 1:]
    tr = np.maximum(h[1:] - l[1:], np.maximum(abs(h[1:] - c[:-1]), abs(l[1:] - c[:-1])))
    atr = np.convolve(tr, np.ones(n) / n, mode="valid")
    k = len(atr)
    hl2, cc = ((h + l) / 2)[-k:], c[-k:]
    up, dn = hl2 + mult * atr, hl2 - mult * atr
    d, fu, fd, prev = 1, up[0], dn[0], 1
    for i in range(1, k):
        fu = up[i] if (up[i] < fu or cc[i - 1] > fu) else fu
        fd = dn[i] if (dn[i] > fd or cc[i - 1] < fd) else fd
        prev = d
        d = 1 if cc[i] > fu else (-1 if cc[i] < fd else d)
    return prev, d


def supertrend(g, b, ctx):
    h, l, c = b[:, 2], b[:, 3], b[:, 4]
    prev, d = _st_dir(h, l, c, int(g["st_n"]), g["st_mult"])
    atr = atr_last(h, l, c)
    if prev < 0 < d:
        return F._build("long", c[-1], atr, g)
    if prev > 0 > d:
        return F._build("short", c[-1], atr, g)


def cluc(g, b, ctx):
    c, v = b[:, 4], b[:, 5]
    n = int(g["bb_n"])
    mid, sd = sma_last(c, n), std_last(c, n)
    if not sd or not np.isfinite(sd):
        return None
    slow = ema_last(c, 50)
    quiet = v[-1] < g["vol_q"] * v[-31:-1].mean()
    atr = atr_last(b[:, 2], b[:, 3], c)
    if quiet and c[-1] < slow and c[-1] < (mid - 2 * sd) * (1 - g["below"]):
        return F._build("long", c[-1], atr, g, target_override=mid)
    if quiet and c[-1] > slow and c[-1] > (mid + 2 * sd) * (1 + g["below"]):
        return F._build("short", c[-1], atr, g, target_override=mid)


FUNCS = {"ewo_dip": ewo_dip, "supertrend": supertrend, "cluc": cluc}


def install():
    """Make the candidates usable by Manager/genome in THIS process only. Live seats are unaffected."""
    live = list(G.FAMILIES)
    G.FAMILY_GENES.update(GENES)
    F.REGISTRY.update(FUNCS)
    assert G.FAMILIES == live, "candidates must never join the live family list"
