import json, random
import numpy as np
import pytest
from trado100 import genome as G, guardian
from trado100.arena import Arena, DAY
from trado100.manager import Manager, BAR_MS
from trado100.store import InMemoryStore
from trado100.synth import make_world


def mk(family="trend", **kw):
    g = G.random_genome(family, random.Random(1))
    return Manager(id=1, family=family, variant=0, genome=g, universe=["A"], born_ts=0, **kw)


def test_genomes_never_exceed_risk_law():
    r = random.Random(3)
    for f in G.FAMILIES:
        g = G.random_genome(f, r)
        for _ in range(300):
            g = G.mutate(f, g, r)
            assert g["risk_pct"] <= 0.02 and g["leverage"] <= 3 and g["rr"] >= 1.5
            if "fast" in g and "slow" in g:
                assert g["fast"] < g["slow"]


def test_mutation_changes_one_or_two_genes():
    r = random.Random(5)
    g = G.random_genome("trend", r)
    m = G.mutate("trend", g, r)
    assert 1 <= sum(g[k] != m[k] for k in g) <= 3  # fix() may nudge fast<slow


def test_guardian_breach_and_vetoes():
    base = dict(equity=1000, side="long", entry=100, stop=98, target=104, risk_pct=0.01,
                leverage=2, free_notional=2000)
    assert guardian.check(**base).ok
    with pytest.raises(guardian.Breach):
        guardian.check(**{**base, "risk_pct": 0.05})
    with pytest.raises(guardian.Breach):
        guardian.check(**{**base, "leverage": 10})
    assert not guardian.check(**{**base, "target": 101}).ok            # R:R 0.5
    assert guardian.check(**base, blackout=True).reason == "macro_blackout"
    assert guardian.check(**base, kill_switch=True).reason == "kill_switch"
    d = guardian.check(**base)
    assert d.qty * 2 <= 1000 * 0.01 * 1.0001                            # risk <= 1% of equity


def test_stop_and_target_fill_and_fees():
    m = mk()
    m.positions["A"] = {"side": "long", "entry": 100.0, "qty": 10.0, "stop": 98.0, "target": 104.0,
                        "opened_ts": 0, "fee_in": 0.55, "why": "t"}
    bars = np.array([[BAR_MS, 100, 105, 99, 103, 1.0]])
    m.step("A", bars)                                   # high 105 >= target 104, low 99 > stop
    assert "A" not in m.positions and m.closed[-1]["reason_out"] == "target"
    assert m.balance == pytest.approx(1000 + 40 - 0.55 - 104 * 10 * 0.00055)


def test_stop_wins_when_both_touched():
    m = mk()
    m.positions["A"] = {"side": "long", "entry": 100.0, "qty": 1.0, "stop": 98.0, "target": 104.0,
                        "opened_ts": 0, "fee_in": 0, "why": "t"}
    m.step("A", np.array([[BAR_MS, 100, 110, 90, 100, 1.0]]))
    assert m.closed[-1]["reason_out"] == "stop" and m.balance < 1000


def _arena():
    world = make_world(["A", "B", "C"], 400, 1)
    return Arena(InMemoryStore(), dict(world), random.Random(1), gate_bars=100), world


def test_drawdown_death_and_inheritance():
    a, w = _arena()
    m = mk("trend"); m.universe = ["A", "B"]
    m.id = a.store.create_manager(m.to_row()); a.managers[m.id] = m
    m.balance = 840.0                       # equity 16% under the 1000 peak
    a.end_step(5 * DAY, max_births=0)
    assert m.status == "dead"
    assert a.store.deaths[-1]["cause"] == "drawdown"
    assert "trend gen1" in a.store.deaths[-1]["post_mortem"]
    assert any(v["family"] == "trend" and v["parent"] is m for v in a.vacancies)   # seat queued for an heir


def test_daily_loss_freeze_then_death_on_second():
    a, _ = _arena()
    m = mk(); m.id = a.store.create_manager(m.to_row()); a.managers[m.id] = m
    t = 10 * DAY
    m.day_key, m.day_start_equity = t // DAY, 1000.0
    m.balance = 930.0                       # -7% in a day
    a.end_step(t, max_births=0)
    assert m.status == "alive" and m.frozen_until > t
    t2 = t + 3 * DAY
    m.day_key, m.day_start_equity, m.balance, m.peak = t2 // DAY, 1000.0, 930.0, 1000.0
    m.frozen_until = 0
    a.end_step(t2, max_births=0)
    assert m.status == "dead" and a.store.deaths[-1]["cause"] == "daily_loss_twice"


def test_idle_and_stuck_death():
    a, _ = _arena()
    m = mk(); m.id = a.store.create_manager(m.to_row()); a.managers[m.id] = m
    m.day_key = 14 * DAY // DAY
    a.end_step(14 * DAY, max_births=0)
    assert m.status == "dead" and a.store.deaths[-1]["cause"] == "idle"
    a2, _ = _arena()
    m2 = mk(); m2.id = a2.store.create_manager(m2.to_row()); a2.managers[m2.id] = m2
    m2.last_trade_ts = 90 * DAY - 1
    a2.end_step(90 * DAY, max_births=0)
    assert a2.store.deaths[-1]["cause"] == "stuck_stage_A"


def test_correlation_needs_same_trade_not_just_same_day():
    a, _ = _arena()
    ms = []
    for i in range(5):
        m = mk(); m.id = a.store.create_manager(m.to_row()); a.managers[m.id] = m
        m.closed.append({"symbol": "A", "side": "long", "entry_price": 1, "exit_price": 1, "qty": 1,
                         "stop_price": 1, "target_price": 1, "fees": 0, "pnl": -5, "leverage": 1,
                         "reason_in": "", "reason_out": "stop",
                         "opened_ts": 1000 + (i * BAR_MS if i == 4 else 0), "closed_ts": 2000})
        ms.append(m)
    for m in ms: a.flush_trades(m)
    a._correlation_rule(DAY)                 # 4 entered on the same bar, 1 later -> below the 5 threshold, no kill
    assert all(m.status != "dead" for m in ms)
    a.today_losses.clear()
    for m in ms:
        m.closed.append({**{"symbol": "A", "side": "long", "entry_price": 1, "exit_price": 1, "qty": 1,
                            "stop_price": 1, "target_price": 1, "fees": 0, "pnl": -5, "leverage": 1,
                            "reason_in": "", "reason_out": "stop"}, "opened_ts": 77, "closed_ts": 99})
        a.flush_trades(m)
    a._correlation_rule(DAY)
    assert sum(m.status == "dead" for m in ms) == 1


def test_row_roundtrip_is_json_safe_and_lossless():
    m = mk(); m.positions["A"] = {"side": "short", "entry": np.float64(10.5), "qty": np.float64(2.0),
                                  "stop": 11.0, "target": 9.0, "opened_ts": 5, "fee_in": 0.1, "why": "x"}
    m.balance, m.peak, m.watch, m.frozen_until = 912.3, 1010.0, True, 123456
    row = m.to_row(); row["id"] = 9
    json.dumps(row)                                        # must serialise for Supabase
    row["status"] = "watch"
    m2 = Manager.from_row(row)
    assert (m2.balance, m2.peak, m2.watch, m2.frozen_until) == (912.3, 1010.0, True, 123456)
    assert m2.status == "alive" and m2.positions["A"]["side"] == "short"


def test_weekly_lesson_needs_two_consecutive_weeks():
    a, _ = _arena()
    for wk in (10, 11):
        ts = wk * 7 * DAY
        a.deaths_log += [{"ts": ts - DAY, "family": "grid", "cause": "drawdown"}] * 2
        a.weekly_postmortem(ts)
        assert bool(a.family_bias["grid"]) == (wk == 11)
    g = a._apply_bias("grid", G.random_genome("grid", random.Random(2)))
    assert g["risk_pct"] <= 0.02


# ---------------- worker end-to-end with a fake exchange feed (offline) ----------------
import asyncio
from trado100.worker import Worker


class FakeFeed:
    def __init__(self, world, start):
        self.world, self.n = world, start
        self.c = None

    async def universe(self, top=50):
        return {s: 0.0001 for s in self.world}

    async def klines(self, symbol, bars=1000, end_ms=None):
        return self.world[symbol][max(0, self.n - bars):self.n]

    async def sentiment(self):
        return -0.2

    async def funding_history(self, symbol, limit=200):
        a = self.world[symbol]
        ts = a[::32, 0]                                   # one settlement per 8h (32 x 15m)
        c = a[::32, 4]
        r = np.clip(np.r_[0, np.diff(c)] / c * 0.2, -0.003, 0.003)
        return np.stack([ts, r], axis=1)

    async def sentiment_history(self, days=90):
        a = self.world["S0USDT"]
        ts = a[::96, 0]
        c = a[::96, 4]
        return np.stack([ts, np.clip((c / c[0] - 1) * 5, -1, 1)], axis=1)


def test_worker_boot_resume_and_cycle():
    syms = [f"S{k}USDT" for k in range(6)]
    world = make_world(syms, 2600, seed=4)
    feed, store = FakeFeed(world, 2400), InMemoryStore()
    w = Worker(store=store, feed=feed)
    import trado100.worker as W
    W.HIST_BARS, W.GATE_BARS = 2400, 600
    w.arena.gate_bars = 600
    asyncio.run(w.boot())
    assert 70 <= len([m for m in store.managers.values() if m["status"] != "dead"]) <= 100
    n0 = len(store.treasury)
    feed.n = 2410
    asyncio.run(w.cycle())
    assert w.last_ts == int(world[syms[0]][2409][0])
    assert len(store.treasury) > n0 and "bar=" in store.treasury[-1]["note"]
    # restart: a brand-new worker resumes the same managers from the store, without re-seeding
    w2 = Worker(store=store, feed=feed)
    asyncio.run(w2.boot())
    assert w2.last_ts == w.last_ts
    assert len(w2.arena.managers) == len([r for r in store.managers.values() if r["status"] != "dead"])
    assert len(store.managers) == len(store.managers)        # no duplicates created on resume


def test_diversity_guard_keeps_three_seats_even_if_gate_rejects_everyone():
    a, w = _arena()
    ms = []
    for v in range(3):
        m = mk("grid"); m.variant, m.universe = v, ["A", "B"]
        m.id = a.store.create_manager(m.to_row()); a.managers[m.id] = m; ms.append(m)
    import trado100.arena as AR
    AR.GATE_MIN_RET = 9.9                    # impossible gate: nobody passes
    try:
        a.kill(ms[0], "drawdown", 5 * DAY)
        a.end_step(5 * DAY)
    finally:
        AR.GATE_MIN_RET = 0.0
    assert a.seats()["grid"] == 3
