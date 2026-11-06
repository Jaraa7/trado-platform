"""Cloud worker — runs on Fly (process `t100`), nonstop, no laptop involved.

    python -m trado100.worker

Every closed 15m bar (+20s): fetch bars -> feed all managers -> death rules -> inheritance ->
persist to Supabase -> heartbeat row in t100_treasury. Survives restarts: state lives in Supabase.
Week-1 limits (by design): bars not ticks (decision latency = 15m); stops checked per bar.
"""
from __future__ import annotations
import asyncio, os, random, re, time
from datetime import datetime, timezone
import httpx
import numpy as np
from loguru import logger

from . import genome as G
from .arena import Arena, DAY
from .feed import Feed, BAR_MS
from .manager import Manager
from .store import SupabaseStore

HIST_BARS = 3000          # ~31 days of 15m bars for the birth gate
GATE_BARS = 2000
KEEP = 4000


class Worker:
    def __init__(self, store=None, feed=None, size_per_family: int = 10):
        self.store = store or SupabaseStore()
        self.feed = feed or Feed()
        self.full: dict[str, np.ndarray] = {}
        self.last_ts = 0
        self.funding: dict[str, float] = {}
        self.sent: float | None = None
        self.arena = Arena(self.store, {}, random.Random(), gate_bars=GATE_BARS,
                           ctx_fn=None, size_per_family=size_per_family)
        self.fh: dict[str, np.ndarray] = {}
        self.sh = np.empty((0, 2))
        self.arena.ctx_fn = self.ctx_fn
        self.n_deaths_notified = 0
        self.last_pm_week = None
        self.fail_cycles = 0

    # ---------------------------------------------------------------- boot
    async def boot(self):
        self.funding = await self.feed.universe(50)
        if not self.funding:
            raise RuntimeError("cannot reach Bybit — will retry")
        rows = self.store.load_alive()
        syms = list(self.funding)
        await self._load_history(syms)
        self.sh = await self.feed.sentiment_history(90)
        for i in range(0, len(syms), 8):
            part = syms[i:i + 8]
            res = await asyncio.gather(*(self.feed.funding_history(x) for x in part))
            self.fh.update(dict(zip(part, res)))
        self.arena.history = {s: self.full[s] for s in syms if s in self.full}
        if rows:
            for r in rows:
                m = Manager.from_row(r)
                self.arena.managers[m.id] = m
            self._recompute_vacancies()
            t = self.store.last_treasury()
            m_ = re.search(r"bar=(\d+)", (t or {}).get("note") or "")
            self.last_ts = int(m_.group(1)) if m_ else max(int(a[-1][0]) for a in self.full.values())
            logger.info(f"resumed {len(rows)} managers, last_bar={self.last_ts}")
        else:
            ts = max(int(a[-1][0]) for a in self.full.values())
            logger.info("fresh start: seeding 100 managers through the backtest gate…")
            self.arena.seed(ts)
            self.last_ts = ts
            logger.info(f"seeded {len(self.arena.managers)} managers, vacancies={len(self.arena.vacancies)}")
        self.arena.persist(self.last_ts)
        self._heartbeat(self.last_ts)

    def ctx_fn(self, sym: str, ts: int) -> dict:
        """Point-in-time funding + sentiment (no look-ahead): last value published at or before ts."""
        out = {}
        f = self.fh.get(sym)
        if f is not None and len(f):
            i = int(np.searchsorted(f[:, 0], ts, side="right")) - 1
            if i >= 0:
                out["funding"] = float(f[i, 1])
        if len(self.sh):
            i = int(np.searchsorted(self.sh[:, 0], ts, side="right")) - 1
            if i >= 0:
                out["sentiment"] = float(self.sh[i, 1])
        return out

    def _recompute_vacancies(self):
        have = {}
        for m in self.arena.managers.values():
            have.setdefault(m.family, set()).add(m.variant)
        self.arena.vacancies = [{"family": f, "variant": v, "tries": 0}
                                for f in G.FAMILIES for v in range(self.arena.size_per_family)
                                if v not in have.get(f, set())]

    async def _load_history(self, syms):
        async def one(s):
            a = await self.feed.klines(s, HIST_BARS)
            if len(a) > 200:
                self.full[s] = a[-KEEP:]
        for i in range(0, len(syms), 8):
            await asyncio.gather(*(one(s) for s in syms[i:i + 8]))

    # ---------------------------------------------------------------- cycle
    async def cycle(self):
        tick = await self.feed.universe(50)
        if tick:
            self.funding = tick
        self.sh = await self.feed.sentiment_history(90)
        await self._refresh_funding()
        syms = sorted({s for m in self.arena.managers.values() if m.status != "dead" for s in m.universe})
        got = 0
        async def one(s):
            nonlocal got
            a = await self.feed.klines(s, 200)
            if len(a):
                got += 1
                old = self.full.get(s)
                if old is not None:
                    a = np.concatenate([old, a])
                    _, idx = np.unique(a[:, 0], return_index=True)
                    a = a[idx]
                self.full[s] = a[-KEEP:]
        for i in range(0, len(syms), 8):
            await asyncio.gather(*(one(s) for s in syms[i:i + 8]))
        if syms and got < 0.5 * len(syms):
            self.arena.blind = True
            self.fail_cycles += 1
            logger.warning(f"blind: only {got}/{len(syms)} symbols fresh")
            return
        self.arena.blind, self.fail_cycles = False, 0

        black = await self._blackout()
        tss = sorted({int(t) for s in syms if s in self.full for t in self.full[s][-300:, 0] if t > self.last_ts})
        for ts in tss:
            self.arena.blackout = black and ts >= tss[-1] - 2 * BAR_MS
            for s in syms:
                a = self.full.get(s)
                if a is None:
                    continue
                i = int(np.searchsorted(a[:, 0], ts))
                if i < len(a) and a[i][0] == ts:
                    self.arena.history[s] = a[:i + 1]
                    self.arena.feed(s, self.ctx_fn(s, ts))
            self.arena.end_step(ts)
        if tss:
            self.last_ts = tss[-1]
            self.arena.persist(self.last_ts)
        self._heartbeat(self.last_ts)
        await self._weekly(datetime.now(timezone.utc))
        await self._notify_deaths()

    async def _refresh_funding(self):
        """Funding settles every 8h: refresh the history only when a settlement could have happened."""
        now = int(time.time() * 1000)
        if now - getattr(self, "_fund_at", 0) < 3600_000:
            return
        self._fund_at = now
        syms = list(self.fh)
        for i in range(0, len(syms), 8):
            part = syms[i:i + 8]
            res = await asyncio.gather(*(self.feed.funding_history(x, 20) for x in part))
            for x, r in zip(part, res):
                if len(r):
                    old = self.fh[x]
                    a = np.concatenate([old, r])
                    _, idx = np.unique(a[:, 0], return_index=True)
                    self.fh[x] = a[idx][-300:]

    async def _blackout(self) -> bool:
        try:
            from data_sources.macro_calendar import MacroCalendar
            return bool((await MacroCalendar.blackout())["blackout"])
        except Exception as e:
            logger.warning(f"macro calendar unavailable: {e}")
            return False

    def _heartbeat(self, ts: int):
        a = self.arena
        live = [m for m in a.managers.values() if m.status != "dead"]
        eq = sum(m.equity() for m in live)
        base = sum(m.start_balance for m in live) or 1
        self.store.save_treasury({"mode": "paper", "equity": round(eq, 4), "peak_equity": round(max(eq, base), 4),
                                  "drawdown": round(max(0.0, 1 - eq / max(eq, base)), 4),
                                  "kill_switch": a.kill_switch,
                                  "note": f"bar={ts} alive={len(live)} vacancies={len(a.vacancies)} "
                                          f"deaths={len(a.deaths_log)} blind={a.blind}"})

    async def _weekly(self, now: datetime):
        wk = now.isocalendar()[:2]
        if now.weekday() == 6 and now.hour >= 9 and self.last_pm_week != wk:
            self.last_pm_week = wk
            self.arena.weekly_postmortem(int(now.timestamp() * 1000))

    async def _notify_deaths(self):
        tok, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_ADMIN_CHAT_ID")
        new = self.arena.deaths_log[self.n_deaths_notified:]
        self.n_deaths_notified = len(self.arena.deaths_log)
        if not (tok and chat and new):
            return
        txt = "💀 TRADO-100: " + "، ".join(f"{d['family']} ({d['cause']})" for d in new[:10])
        try:
            await self.feed.c.post(f"https://api.telegram.org/bot{tok}/sendMessage",
                                   json={"chat_id": chat, "text": txt})
        except httpx.HTTPError:
            pass

    # ---------------------------------------------------------------- loop
    async def run(self):
        while True:
            try:
                await self.boot()
                break
            except Exception as e:
                logger.error(f"boot failed: {e}; retry in 60s")
                await asyncio.sleep(60)
        while True:
            now = time.time() * 1000
            wait = (BAR_MS - now % BAR_MS) / 1000 + 20
            await asyncio.sleep(wait)
            try:
                await self.cycle()
            except Exception as e:                      # never die: guardian restarts only if silent
                logger.exception(f"cycle failed: {e}")


if __name__ == "__main__":
    asyncio.run(Worker().run())
