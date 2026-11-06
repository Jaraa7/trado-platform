"""The population: 100 managers, nonstop. Death rules, inheritance, evolution, gate."""
from __future__ import annotations
import random
from typing import Callable, Dict, List, Optional
import numpy as np

from . import genome as G, guardian
from .manager import Manager, BAR_MS, STAGE_CAPITAL
from .store import _iso, trade_row

DAY = 86_400_000
GATE_MIN_TRADES = 3
GATE_MIN_RET = 0.0
GATE_MAX_DD = 0.12
SYMS_PER_MANAGER = 5


def backtest_gate(proto: Manager, history: Dict[str, np.ndarray], n_bars: int,
                  ctx_fn: Optional[Callable] = None) -> dict:
    """Run a fresh copy of `proto` over the last n_bars. Same step() as live."""
    m = Manager(id=-1, family=proto.family, variant=proto.variant, genome=dict(proto.genome),
                universe=list(proto.universe))
    syms = [s for s in m.universe if s in history]
    if not syms:
        return {"ok": False, "ret": 0, "trades": 0, "dd": 1}
    L = {s: len(history[s]) for s in syms}
    n = min(n_bars, min(L.values()) - 1)
    peak, mdd = m.equity(), 0.0
    for j in range(n):
        for s in syms:
            idx = L[s] - n + j
            m.step(s, history[s][:idx + 1], ctx_fn(s, int(history[s][idx][0])) if ctx_fn else None)
        eq = m.equity()
        peak = max(peak, eq)
        mdd = max(mdd, (peak - eq) / peak)
    m.close_all(0, "gate_end")
    ret = (m.balance - 1000) / 1000
    return {"ok": ret > GATE_MIN_RET and m.n_trades >= GATE_MIN_TRADES and mdd < GATE_MAX_DD,
            "ret": ret, "trades": m.n_trades, "dd": mdd}


class Arena:
    def __init__(self, store, history: Dict[str, np.ndarray], rng: Optional[random.Random] = None,
                 gate_bars: int = 2880, ctx_fn: Optional[Callable] = None, size_per_family: int = 10):
        self.store, self.history, self.rng = store, history, rng or random.Random()
        self.gate_bars, self.ctx_fn = gate_bars, ctx_fn
        self.size_per_family = size_per_family
        self.managers: Dict[int, Manager] = {}
        self.vacancies: List[dict] = []         # [{"family","variant","tries"}]
        self.family_bias: Dict[str, List[dict]] = {f: [] for f in G.FAMILIES}
        self.pending_lessons: Dict[tuple, int] = {}
        self.deaths_log: List[dict] = []        # in-memory mirror for weekly post-mortem
        self.today_losses: Dict[tuple, set] = {}
        self.kill_switch = False
        self.blind = False
        self.blackout = False

    # ------------------------------------------------------------------ birth
    def _pool(self) -> List[str]:
        return list(self.history)

    def _new_proto(self, family: str, variant: int, genome: dict, parent: Optional[Manager], ts: int) -> Manager:
        pool = self._pool()
        uni = self.rng.sample(pool, k=min(SYMS_PER_MANAGER, len(pool)))
        m = Manager(id=0, family=family, variant=variant, genome=genome, universe=uni,
                    generation=(parent.generation + 1) if parent else 1,
                    parent_id=parent.id if parent else None, born_ts=ts, stage_since=ts, day_key=ts // DAY)
        return m

    def _apply_bias(self, family: str, g: dict) -> dict:
        g = dict(g)
        for b in self.family_bias.get(family, []):
            if "risk_mult" in b:
                g["risk_pct"] = g["risk_pct"] * b["risk_mult"]
        return G.fix(family, g)

    def _birth(self, proto: Manager) -> Manager:
        row = proto.to_row()
        row["status"] = "alive"
        proto.id = self.store.create_manager(row)
        proto.lessons = [b["text"] for b in self.family_bias.get(proto.family, [])]
        self.managers[proto.id] = proto
        return proto

    def seed(self, ts: int, max_tries: int = 25):
        """100 managers: 10 families x 10 variants, each born only if it survives the gate."""
        for fam in G.FAMILIES:
            for v in range(self.size_per_family):
                if not self._spawn(fam, v, None, ts, max_tries):
                    self.vacancies.append({"family": fam, "variant": v, "tries": 0})

    def _spawn(self, family: str, variant: int, parent: Optional[Manager], ts: int, max_tries: int) -> Optional[Manager]:
        survivors = sorted((m for m in self.managers.values() if m.family == family and m.status != "dead"),
                           key=lambda m: m.equity(), reverse=True)
        for _ in range(max_tries):
            r = self.rng.random()
            if parent is not None and r < 0.6:
                g = G.mutate(family, parent.genome, self.rng)
            elif len(survivors) >= 2 and r < 0.8:
                g = G.crossover(family, survivors[0].genome, survivors[1].genome, self.rng)
            elif survivors and r < 0.9:
                g = G.mutate(family, survivors[0].genome, self.rng)
            else:
                g = G.random_genome(family, self.rng)
            g = self._apply_bias(family, g)
            proto = self._new_proto(family, variant, g, parent, ts)
            res = backtest_gate(proto, self.history, self.gate_bars, self.ctx_fn)
            if res["ok"]:
                return self._birth(proto)
        return None

    # ------------------------------------------------------------------ feeding
    def feed(self, sym: str, ctx: Optional[dict] = None):
        bars = self.history[sym]
        for m in self.managers.values():
            if m.status != "dead" and sym in m.universe:
                m.step(sym, bars, ctx, blackout=self.blackout, blind=self.blind, kill=self.kill_switch)

    # ------------------------------------------------------------------ death
    def kill(self, m: Manager, cause: str, ts: int):
        if m.status == "dead":
            return
        m.close_all(ts, f"death:{cause}")
        eq = m.balance
        ret = (eq - m.start_balance) / m.start_balance
        wr = (m.wins / m.n_trades) if m.n_trades else 0.0
        age = (ts - m.born_ts) / DAY
        pm = (f"{m.family} gen{m.generation} (stage {m.stage}) died: {cause}. age={age:.1f}d "
              f"trades={m.n_trades} winrate={wr:.0%} return={ret:+.1%} maxDD_stage={m.max_dd_stage:.1%} "
              f"genome={m.genome}")
        m.status = "dead"
        self.flush_trades(m)
        row = m.to_row()
        row.update({"id": m.id, "status": "dead", "balance": round(eq, 4)})
        self.store.update_managers([row])
        death = {"manager_id": m.id, "cause": cause, "final_balance": round(eq, 4),
                 "max_drawdown": round(m.max_dd_stage, 4), "trades_count": m.n_trades, "post_mortem": pm}
        self.store.save_death(death)
        self.deaths_log.append({"ts": ts, "family": m.family, "cause": cause})
        self.vacancies.append({"family": m.family, "variant": m.variant, "tries": 0, "parent": m})

    def flush_trades(self, m: Manager):
        if m.closed:
            self.store.insert_trades([trade_row(m.id, t) for t in m.closed])
            for t in m.closed:
                if t["pnl"] < 0:  # "same trade" = same symbol, same side, entered on the same bar
                    key = (m.family, t["symbol"], t["side"], t["opened_ts"])
                    self.today_losses.setdefault(key, set()).add(m.id)
            m.closed.clear()
        m.opened.clear()

    # ------------------------------------------------------------------ per-step rules
    def end_step(self, ts: int, max_births: int = 5):
        for m in list(self.managers.values()):
            if m.status == "dead":
                continue
            eq = m.equity()
            m.peak = max(m.peak, eq)
            dd = (m.peak - eq) / m.peak if m.peak > 0 else 1.0
            m.max_dd_stage = max(m.max_dd_stage, dd)
            # --- new UTC day bookkeeping
            dk = ts // DAY
            if dk != m.day_key:
                m.day_key, m.day_start_equity = dk, eq
                m.eq_hist = [h for h in m.eq_hist if dk - h[0] <= 35] + [[dk, eq]]
                base = next((h[1] for h in m.eq_hist if dk - h[0] >= 28), None)
                m.watch = bool(base and eq / base - 1 > 0.40)
            # --- rules (order = severity)
            if dd >= guardian.MAX_DRAWDOWN:
                self.kill(m, "drawdown", ts); continue
            if eq <= m.day_start_equity * (1 - guardian.DAILY_LOSS_FREEZE) and ts >= m.frozen_until:
                m.close_all(ts, "daily_loss_freeze")
                recent = [t for t in m.freeze_log if ts - t < 7 * DAY]
                m.freeze_log = recent + [ts]
                m.frozen_until = ts + DAY
                if len(m.freeze_log) >= 2:
                    self.kill(m, "daily_loss_twice", ts); continue
            if ts - max(m.last_trade_ts, m.born_ts) >= 14 * DAY:
                self.kill(m, "idle", ts); continue
            if m.stage == "A" and ts - m.stage_since >= 90 * DAY:
                self.kill(m, "stuck_stage_A", ts); continue
            self._maybe_promote(m, eq, ts)
        if (ts // BAR_MS) % 96 == 95:      # last bar of the UTC day
            self._correlation_rule(ts)
        for m in self.managers.values():
            if m.status != "dead":
                self.flush_trades(m)
        self._refill(ts, max_births)

    def _maybe_promote(self, m: Manager, eq: float, ts: int):
        if m.stage == "A" and eq >= 1200 and ts - m.stage_since <= 60 * DAY and m.max_dd_stage <= 0.10 and m.n_trades >= 30:
            self._promote(m, "B", ts)
        elif m.stage == "B" and eq >= 3000 and m.max_dd_stage <= 0.12 and ts - m.born_ts >= 90 * DAY:
            self._promote(m, "C", ts)

    def _promote(self, m: Manager, stage: str, ts: int):
        m.close_all(ts, f"promote:{stage}")
        m.stage = stage
        m.start_balance = m.balance = m.peak = STAGE_CAPITAL[stage]
        m.stage_since, m.max_dd_stage, m.day_start_equity = ts, 0.0, m.balance

    def _correlation_rule(self, ts: int):
        fams = {}
        for (fam, _sym, _side, _opened), ids in self.today_losses.items():
            if len(ids) >= 3:
                fams.setdefault(fam, set()).update(ids)
        for fam, ids in fams.items():
            cands = [self.managers[i] for i in ids if self.managers[i].status != "dead"]
            if cands:
                self.kill(min(cands, key=lambda x: x.equity() / x.start_balance), "correlation", ts)
        self.today_losses.clear()

    # ------------------------------------------------------------------ inheritance
    def _refill(self, ts: int, max_births: int):
        done = 0
        remaining = []
        for v in self.vacancies:
            if done >= max_births:
                remaining.append(v); continue
            fam, parent = v["family"], v.get("parent")
            if parent is None:
                live = [m for m in self.managers.values() if m.family == fam and m.status != "dead"]
                parent = max(live, key=lambda x: x.equity()) if live else None
            heir = self._spawn(fam, v["variant"], parent, ts, max_tries=12)
            done += 1
            if heir is None:
                v["tries"] += 1
                remaining.append(v)
        self.vacancies = remaining

    def seats(self) -> Dict[str, int]:
        out = {f: 0 for f in G.FAMILIES}
        for m in self.managers.values():
            if m.status != "dead":
                out[m.family] += 1
        return out

    # ------------------------------------------------------------------ weekly post-mortem
    def weekly_postmortem(self, ts: int):
        """A lesson becomes active only when two consecutive weekly post-mortems agree."""
        week = ts // (7 * DAY)
        recent = [d for d in self.deaths_log if ts - d["ts"] <= 7 * DAY]
        counts: Dict[tuple, int] = {}
        for d in recent:
            counts[(d["family"], d["cause"])] = counts.get((d["family"], d["cause"]), 0) + 1
        for (fam, cause), n in counts.items():
            if n < 2:
                continue
            if self.pending_lessons.get((fam, cause)) == week - 1:
                text = f"{fam}: repeated deaths by {cause} two weeks running"
                bias = {"text": text}
                if cause in ("drawdown", "daily_loss_twice"):
                    bias["risk_mult"] = 0.8
                if text not in [b["text"] for b in self.family_bias[fam]]:
                    self.family_bias[fam].append(bias)
                    self.store.save_lesson({"family": fam, "lesson": text, "confirmations": 2, "active": True})
            self.pending_lessons[(fam, cause)] = week
        return counts

    # ------------------------------------------------------------------ persistence of live state
    def persist(self, ts: int):
        rows = []
        for m in self.managers.values():
            if m.status == "dead":
                continue
            r = m.to_row()
            r["id"] = m.id
            r["status"] = "watch" if m.watch else "alive"
            r["balance"], r["peak_balance"] = round(m.balance, 4), round(m.peak, 4)
            r["frozen_until"] = _iso(m.frozen_until)
            r["last_trade_at"] = _iso(m.last_trade_ts)
            r.pop("born_at", None)  # DB default; never overwrite
            rows.append(r)
        self.store.update_managers(rows)

    def treasury_snapshot(self, ts: int):
        live = [m for m in self.managers.values() if m.status != "dead"]
        eq = sum(m.equity() for m in live)
        base = sum(m.start_balance for m in live)
        self.store.save_treasury({"mode": "paper", "equity": round(eq, 4),
                                  "peak_equity": round(max(eq, base), 4),
                                  "drawdown": round(max(0.0, 1 - eq / max(eq, base)), 4),
                                  "kill_switch": self.kill_switch,
                                  "note": f"alive={len(live)} vacancies={len(self.vacancies)}"})
