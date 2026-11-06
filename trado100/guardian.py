"""Risk Guardian — the law. Pure math, no I/O, no LLM. Every order passes through check()."""
from __future__ import annotations
from dataclasses import dataclass

MAX_RISK_PCT = 0.02
MIN_RR = 1.5
MAX_LEVERAGE = 3
DAILY_LOSS_FREEZE = 0.06
MAX_DRAWDOWN = 0.15
MAX_SEATS_PER_FAMILY = 30
MIN_SEATS_PER_FAMILY = 3


class Breach(Exception):
    """A manager asked for more than the law allows -> the manager dies ('rule_breach')."""


@dataclass
class Decision:
    ok: bool
    qty: float = 0.0
    reason: str = ""


def check(*, equity: float, side: str, entry: float, stop: float, target: float,
          risk_pct: float, leverage: float, free_notional: float,
          blackout: bool = False, blind: bool = False, frozen: bool = False,
          kill_switch: bool = False) -> Decision:
    # --- breaches: asking for more than the law allows is fatal, not just rejected
    if risk_pct > MAX_RISK_PCT + 1e-12:
        raise Breach(f"risk_pct {risk_pct} > {MAX_RISK_PCT}")
    if leverage > MAX_LEVERAGE:
        raise Breach(f"leverage {leverage} > {MAX_LEVERAGE}")
    # --- soft vetoes
    if kill_switch:
        return Decision(False, reason="kill_switch")
    if frozen:
        return Decision(False, reason="frozen")
    if blind:
        return Decision(False, reason="blind_feed")
    if blackout:
        return Decision(False, reason="macro_blackout")
    stop_d = abs(entry - stop)
    if stop_d <= 0 or equity <= 0:
        return Decision(False, reason="bad_stop_or_equity")
    if (side == "long" and not stop < entry < target) or (side == "short" and not target < entry < stop):
        return Decision(False, reason="bad_geometry")
    rr = abs(target - entry) / stop_d
    if rr < MIN_RR - 1e-9:
        return Decision(False, reason=f"rr {rr:.2f} < {MIN_RR}")
    qty = equity * risk_pct / stop_d
    max_qty_by_lev = min(equity * leverage, max(free_notional, 0.0)) / entry
    qty = min(qty, max_qty_by_lev)
    if qty * entry < 5:  # below Bybit practical minimum notional
        return Decision(False, reason="size_too_small")
    return Decision(True, qty=qty)
