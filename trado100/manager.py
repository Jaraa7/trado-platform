"""A manager = state + one shared `step()` used by live, paper and gate-backtests alike."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np

from . import families, guardian
from .indicators import resample

BAR_MS = 15 * 60 * 1000
SLIPPAGE = 0.001      # 0.1%
TAKER_FEE = 0.00055   # Bybit linear taker
MAX_OPEN = 3

STAGE_CAPITAL = {"A": 1000.0, "B": 2000.0, "C": 5000.0}


@dataclass
class Manager:
    id: int
    family: str
    variant: int
    genome: dict
    universe: List[str]
    generation: int = 1
    parent_id: Optional[int] = None
    status: str = "alive"            # born|alive|frozen|watch|dead
    stage: str = "A"
    start_balance: float = 1000.0
    balance: float = 1000.0          # cash incl. realised pnl (unrealised excluded)
    peak: float = 1000.0
    born_ts: int = 0
    last_trade_ts: int = 0
    frozen_until: int = 0
    freeze_log: List[int] = field(default_factory=list)
    day_key: int = -1
    day_start_equity: float = 1000.0
    stage_since: int = 0
    max_dd_stage: float = 0.0
    positions: Dict[str, dict] = field(default_factory=dict)
    last_px: Dict[str, float] = field(default_factory=dict)
    n_trades: int = 0
    wins: int = 0
    lessons: List[str] = field(default_factory=list)
    eq_hist: List[list] = field(default_factory=list)   # [[day_key, equity]] last 35 days
    watch: bool = False
    closed: List[dict] = field(default_factory=list)    # trades closed since last persist
    opened: List[dict] = field(default_factory=list)

    # ------------------------------------------------------------------ equity
    def equity(self) -> float:
        eq = self.balance
        for sym, p in self.positions.items():
            px = self.last_px.get(sym, p["entry"])
            eq += (px - p["entry"]) * p["qty"] * (1 if p["side"] == "long" else -1)
        return eq

    def _notional_open(self) -> float:
        return sum(p["entry"] * p["qty"] for p in self.positions.values())

    # ------------------------------------------------------------------ trading
    def _close(self, sym: str, px: float, ts: int, reason: str):
        p = self.positions.pop(sym)
        d = 1 if p["side"] == "long" else -1
        fee_out = px * p["qty"] * TAKER_FEE
        pnl = (px - p["entry"]) * p["qty"] * d - p["fee_in"] - fee_out
        self.balance += pnl
        self.n_trades += 1
        self.wins += 1 if pnl > 0 else 0
        self.last_trade_ts = ts
        self.closed.append({"symbol": sym, "side": p["side"], "entry_price": p["entry"], "exit_price": px,
                            "qty": p["qty"], "stop_price": p["stop"], "target_price": p["target"],
                            "fees": p["fee_in"] + fee_out, "pnl": pnl, "leverage": self.genome["leverage"],
                            "reason_in": p.get("why", ""), "reason_out": reason,
                            "opened_ts": p["opened_ts"], "closed_ts": ts})
        return pnl

    def close_all(self, ts: int, reason: str):
        for sym in list(self.positions):
            px = self.last_px.get(sym, self.positions[sym]["entry"])
            d = -1 if self.positions[sym]["side"] == "long" else 1
            self._close(sym, px * (1 + d * SLIPPAGE), ts, reason)

    def step(self, sym: str, bars15: np.ndarray, ctx: Optional[dict] = None,
             blackout: bool = False, blind: bool = False, kill: bool = False):
        """Process the newest CLOSED 15m bar of `sym` (bars15[-1])."""
        if self.status == "dead":
            return
        bar = bars15[-1]
        ts, hi, lo, close = int(bar[0]), bar[2], bar[3], bar[4]
        self.last_px[sym] = close
        # --- exits first (stop wins if both touched in one bar: conservative)
        p = self.positions.get(sym)
        if p and ts > p["opened_ts"]:
            if p["side"] == "long":
                if lo <= p["stop"]:
                    self._close(sym, p["stop"] * (1 - SLIPPAGE), ts, "stop")
                elif hi >= p["target"]:
                    self._close(sym, p["target"], ts, "target")
            else:
                if hi >= p["stop"]:
                    self._close(sym, p["stop"] * (1 + SLIPPAGE), ts, "stop")
                elif lo <= p["target"]:
                    self._close(sym, p["target"], ts, "target")
        # --- entries
        if sym in self.positions or len(self.positions) >= MAX_OPEN or self.status != "alive":
            return
        tf = self.genome["tf"]
        if tf > 1 and (ts // BAR_MS) % tf != tf - 1:
            return
        sig = families.signal(self.family, self.genome, resample(bars15, tf), ctx)
        if not sig:
            return
        side = sig["side"]
        entry = close * (1 + SLIPPAGE if side == "long" else 1 - SLIPPAGE)
        dec = guardian.check(
            equity=self.equity(), side=side, entry=entry, stop=sig["stop"], target=sig["target"],
            risk_pct=self.genome["risk_pct"], leverage=self.genome["leverage"],
            free_notional=self.equity() * self.genome["leverage"] - self._notional_open(),
            blackout=blackout, blind=blind, frozen=ts < self.frozen_until, kill_switch=kill)
        if not dec.ok:
            return
        fee_in = entry * dec.qty * TAKER_FEE
        self.positions[sym] = {"side": side, "entry": entry, "qty": dec.qty, "stop": sig["stop"],
                               "target": sig["target"], "opened_ts": ts, "fee_in": fee_in,
                               "why": f"{self.family}"}
        self.opened.append({"symbol": sym, "side": side, "entry_price": entry, "qty": dec.qty})

    # ------------------------------------------------------------------ persistence
    def to_row(self) -> dict:
        return {
            "family": self.family, "variant": self.variant, "generation": self.generation,
            "parent_id": self.parent_id, "status": self.status, "stage": self.stage,
            "genome": self.genome, "universe": self.universe,
            "risk_profile": {"risk_pct": self.genome["risk_pct"], "leverage": self.genome["leverage"]},
            "brain": {
                "positions": self.positions, "freeze_log": self.freeze_log, "day_key": self.day_key,
                "day_start_equity": self.day_start_equity, "stage_since": self.stage_since,
                "max_dd_stage": self.max_dd_stage, "last_px": self.last_px, "n_trades": self.n_trades,
                "wins": self.wins, "lessons": self.lessons, "eq_hist": self.eq_hist, "watch": self.watch,
                "born_ts": self.born_ts, "last_trade_ts": self.last_trade_ts, "frozen_until": self.frozen_until,
            },
            "start_balance": self.start_balance, "balance": round(self.balance, 4),
            "peak_balance": round(self.peak, 4),
        }  # born_at/frozen_until/last_trade_at are never sent here: born_at is NOT NULL with a DB default

    @classmethod
    def from_row(cls, r: dict) -> "Manager":
        b = r.get("brain") or {}
        watch = b.get("watch", False) or r["status"] == "watch"
        return cls(
            id=r["id"], family=r["family"], variant=r["variant"], genome=r["genome"],
            universe=r["universe"], generation=r["generation"], parent_id=r.get("parent_id"),
            status="alive" if r["status"] == "watch" else r["status"], stage=r["stage"], start_balance=float(r["start_balance"]),
            balance=float(r["balance"]), peak=float(r["peak_balance"]),
            born_ts=b.get("born_ts", 0), last_trade_ts=b.get("last_trade_ts", 0),
            frozen_until=b.get("frozen_until", 0), freeze_log=b.get("freeze_log", []),
            day_key=b.get("day_key", -1), day_start_equity=b.get("day_start_equity", float(r["balance"])),
            stage_since=b.get("stage_since", 0), max_dd_stage=b.get("max_dd_stage", 0.0),
            positions=b.get("positions", {}), last_px=b.get("last_px", {}), n_trades=b.get("n_trades", 0),
            wins=b.get("wins", 0), lessons=b.get("lessons", []), eq_hist=b.get("eq_hist", []),
            watch=watch,
        )
