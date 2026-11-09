"""Genomes: bounded numeric genes per family; mutation (±10–20% on 1–2 genes) and crossover.

Every gene has hard (lo, hi) bounds, so evolution can never produce a genome that
exceeds the Risk Guardian limits (risk_pct <= 2%, leverage <= 3).
"""
from __future__ import annotations
import random
from typing import Dict, Tuple

Gene = Tuple[float, float, bool]  # lo, hi, is_int

COMMON: Dict[str, Gene] = {
    "tf":        (1, 4, True),       # timeframe multiplier over 15m bars: 1 (15m) .. 4 (1h)
    "risk_pct":  (0.003, 0.02, False),
    "leverage":  (1, 3, True),
    "atr_stop":  (1.2, 3.5, False),
    "rr":        (1.5, 3.5, False),
}

FAMILY_GENES: Dict[str, Dict[str, Gene]] = {
    "trend":          {"fast": (6, 24, True), "slow": (28, 90, True), "rsi_min": (45, 58, False)},
    "breakout":       {"lookback": (15, 70, True), "vol_mult": (1.0, 2.2, False)},
    "mean_reversion": {"bb_n": (14, 32, True), "bb_k": (1.8, 2.8, False), "rsi_lo": (18, 38, False)},
    "scalp":          {"fast": (3, 7, True), "slow": (9, 16, True), "vol_spike": (1.2, 2.5, False)},
    "grid":           {"n": (20, 60, True), "step_atr": (0.8, 2.2, False)},
    "funding_basis":  {"thr": (0.0002, 0.0012, False), "hold_ema": (10, 40, True)},
    "regime_switch":  {"er_n": (10, 30, True), "er_thr": (0.25, 0.5, False), "fast": (8, 20, True), "slow": (30, 70, True)},
    "sentiment":      {"extreme": (0.4, 0.85, False), "confirm_n": (5, 20, True)},
    "accumulate":     {"n": (30, 90, True), "dip_pct": (0.01, 0.05, False)},
    "llm_judge":      {"votes_needed": (2, 3, True), "cooldown": (4, 16, True)},
}

FAMILIES = list(FAMILY_GENES)
# tf is forced to 1 (>=15m) for scalp; the LLM judge works on >=1h only (tf=4).
FORCED = {"scalp": {"tf": 1}, "llm_judge": {"tf": 4}}


def spec(family: str) -> Dict[str, Gene]:
    return {**COMMON, **FAMILY_GENES[family]}


def _clip(v: float, g: Gene) -> float:
    lo, hi, is_int = g
    v = min(max(v, lo), hi)
    return int(round(v)) if is_int else round(v, 6)


def random_genome(family: str, rng: random.Random) -> dict:
    out = {}
    for k, g in spec(family).items():
        lo, hi, is_int = g
        out[k] = _clip(rng.uniform(lo, hi), g)
    out.update(FORCED.get(family, {}))
    return fix(family, out)


def fix(family: str, genome: dict) -> dict:
    """Enforce cross-gene constraints (fast < slow etc.) and hard risk bounds."""
    s = spec(family)
    g = {k: _clip(genome[k], s[k]) for k in s}
    g.update(FORCED.get(family, {}))
    if "fast" in g and "slow" in g and g["fast"] >= g["slow"]:
        g["fast"] = max(int(s["fast"][0]), int(g["slow"]) - 3)
    g["risk_pct"] = min(g["risk_pct"], 0.02)
    g["leverage"] = min(int(g["leverage"]), 3)
    return g


def mutate(family: str, genome: dict, rng: random.Random) -> dict:
    """±10–20% on 1–2 genes."""
    g = dict(genome)
    s = spec(family)
    free = [k for k in s if k not in FORCED.get(family, {})]
    for k in rng.sample(free, k=rng.choice([1, 2])):
        delta = rng.uniform(0.10, 0.20) * rng.choice([-1, 1])
        lo, hi, is_int = s[k]
        new = g[k] * (1 + delta)
        if is_int and int(round(new)) == g[k]:  # make sure integer genes really move
            new = g[k] + rng.choice([-1, 1])
        g[k] = _clip(new, s[k])
    return fix(family, g)


def crossover(family: str, a: dict, b: dict, rng: random.Random) -> dict:
    return fix(family, {k: (a[k] if rng.random() < 0.5 else b[k]) for k in spec(family)})


def distance(family: str, a: dict, b: dict) -> float:
    """Mean normalised gene difference in [0,1] over the family's free genes (0 = identical)."""
    sp = spec(family)
    free = [k for k in sp if k not in FORCED.get(family, {})]
    if not free:
        return 1.0
    tot = 0.0
    for k in free:
        lo, hi, _ = sp[k]
        tot += abs(float(a[k]) - float(b[k])) / ((hi - lo) or 1.0)
    return tot / len(free)
