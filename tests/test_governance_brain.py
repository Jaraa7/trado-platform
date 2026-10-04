"""الحوكمة + سجل القرارات + الدماغ + أوامر المالك — بلا شبكة."""
import asyncio
import pytest

from governance.limits import LIMITS
from governance.killswitch import KillSwitch, assert_not_stopped
from governance.budget import AIBudget
from nervous.decisions import DecisionLog
from nervous.scheduler import Brain, EXCLUDED_SYMBOLS_KEY, PAUSED_AGENTS_KEY
from nervous.owner_commands import OwnerCommands
from nervous.performance import PerformanceTracker, MIN_SAMPLE


class FakeRedis:
    def __init__(self): self.d = {}
    def get(self, k): return self.d.get(k)
    def set(self, k, v): self.d[k] = v
    def ping(self): return True


@pytest.fixture
def ks():
    return KillSwitch(redis_client=FakeRedis())


@pytest.fixture
def log(tmp_path, monkeypatch):
    monkeypatch.setenv("NERVOUS_DECISIONS_FILE", str(tmp_path / "d.json"))
    import nervous.decisions as m
    monkeypatch.setattr(m, "_FILE", tmp_path / "d.json")
    return DecisionLog(use_db=False)


class TestLimits:
    def test_approved_caps(self):
        assert LIMITS.ai_monthly_usd == 100 and LIMITS.fly_monthly_usd == 25
        assert LIMITS.max_daily_loss_pct == 3 and LIMITS.max_monthly_drawdown_pct == 8
        assert "governance/" in LIMITS.protected_paths
        with pytest.raises(Exception):
            LIMITS.ai_monthly_usd = 999  # frozen


class TestKillSwitch:
    def test_stop_resume(self, ks):
        assert not ks.is_stopped()
        ks.stop("test", by="owner")
        assert ks.is_stopped() and ks.state()["reason"] == "test"
        with pytest.raises(RuntimeError, match="موقوف"):
            assert_not_stopped(ks)
        ks.resume(by="owner")
        assert not ks.is_stopped()

    def test_redis_failure_fails_safe(self):
        class Broken:
            def get(self, k): raise ConnectionError("down")
            def ping(self): return True
        assert KillSwitch(redis_client=Broken()).is_stopped() is True


class TestBudget:
    def test_status_and_exceeded(self):
        b = AIBudget(spent_reader=lambda: 85.0, cache_ttl_s=0)
        s = b.status(); assert s["warn"] and not s["exceeded"]
        assert AIBudget(spent_reader=lambda: 100.0, cache_ttl_s=0).exceeded()
        assert not AIBudget(spent_reader=lambda: (_ for _ in ()).throw(RuntimeError("db")), cache_ttl_s=0).exceeded()


class TestDecisions:
    def test_levels_and_flow(self, log):
        d0 = log.propose("t", 0, "exclude_symbol", "X/USDT", "r", {})
        assert d0["status"] == "approved"
        log.mark_executed(d0["id"]); assert log.get(d0["id"])["status"] == "executed"
        d2 = log.propose("t", 2, "promote_candidate", "agent", "r", {})
        assert d2["status"] == "proposed" and len(log.pending()) == 1
        log.approve(d2["id"][:8], by="owner"); assert log.get(d2["id"])["status"] == "approved"
        with pytest.raises(ValueError):
            log.approve(d2["id"], by="owner")
        log.revert(d0["id"], by="owner"); assert log.get(d0["id"])["status"] == "reverted"

    def test_expire_stale(self, log):
        d = log.propose("t", 2, "x", "y", "r", {})
        log._update(d["id"], created_at="2020-01-01T00:00:00+00:00")
        assert log.expire_stale() == 1 and log.pending() == []


def _rows(agent, n, r, sym="BTC/USDT"):
    return [{"generated_by": agent, "symbol": sym, "status": "hit_tp" if r > 0 else "hit_sl", "r_multiple": r}
            for _ in range(n)]


class FakeMarket:
    def __init__(self, ok=True): self.ok = ok
    async def brief(self):
        return {"data_ok": self.ok, "btc_regime": {"regime": "ranging"},
                "posture": {"size_multiplier": 0.5, "favor": ["mean_reversion"]}}


class TestBrain:
    def _brain(self, ks, log, rows, msgs):
        return Brain(killswitch=ks, budget=AIBudget(spent_reader=lambda: 10.0, cache_ttl_s=0), decisions=log,
                     market=FakeMarket(), tracker_factory=lambda: PerformanceTracker(rows),
                     notify=msgs.append, state_store={})

    def test_tick_applies_levels(self, ks, log):
        msgs = []
        rows = _rows("loser", 25, -1) + _rows("winner", 20, 2) + _rows("winner", 5, -1) \
             + _rows("w2", 25, -1, sym="DOGE/USDT")
        b = self._brain(ks, log, rows, msgs)
        t = asyncio.run(b.tick())
        assert t["size_multiplier"] == 0.5
        assert "loser" in b.state[PAUSED_AGENTS_KEY]            # درجة 1 نُفِّذ + أُبلغ
        assert "DOGE/USDT" in b.state[EXCLUDED_SYMBOLS_KEY]      # درجة 0 نُفِّذ بصمت
        assert len(log.pending()) == 1                            # winner → درجة 2 بانتظارك
        assert any("طلب موافقة" in m for m in msgs) and any("درجة 1" in m for m in msgs)

    def test_tick_respects_killswitch(self, ks, log):
        msgs = []
        ks.stop("maintenance", by="owner")
        b = self._brain(ks, log, _rows("a", 30, -1), msgs)
        t = asyncio.run(b.tick())
        assert t["skipped"] and log.pending() == [] and b.state == {}

    def test_small_sample_only_observes(self, ks, log):
        msgs = []
        b = self._brain(ks, log, _rows("a", MIN_SAMPLE - 1, 1), msgs)
        asyncio.run(b.tick())
        assert msgs == [] and PAUSED_AGENTS_KEY not in b.state
        assert "ملخص اليوم" in b.daily_summary()


class TestOwnerCommands:
    def test_non_owner_ignored(self, ks, log, monkeypatch):
        monkeypatch.setenv("TELEGRAM_ADMIN_CHAT_ID", "111")
        oc = OwnerCommands(ks=ks, log=log, budget=AIBudget(spent_reader=lambda: 0, cache_ttl_s=0))
        assert oc.handle(222, "/stop") is None and not ks.is_stopped()

    def test_owner_flow(self, ks, log, monkeypatch):
        monkeypatch.setenv("TELEGRAM_ADMIN_CHAT_ID", "111")
        oc = OwnerCommands(ks=ks, log=log, budget=AIBudget(spent_reader=lambda: 0, cache_ttl_s=0))
        assert "تم الإيقاف" in oc.handle(111, "/stop سوق مجنون") and ks.is_stopped()
        assert "موقوف" in oc.handle(111, "/status")
        assert "الاستئناف" in oc.handle(111, "/resume") and not ks.is_stopped()
        d = log.propose("t", 2, "promote_candidate", "winner", "r", {})
        assert d["id"][:8] in oc.handle(111, "/pending")
        assert "الموافقة" in oc.handle(111, f"/approve_{d['id'][:8]}")
        assert "⚠️" in oc.handle(111, f"/approve_{d['id'][:8]}")
        assert oc.handle(111, "/signals") is None   # أمر عادي يمرّ للبوت


class TestExecutionerGates:
    def test_live_blocked_in_paper_phase(self, monkeypatch):
        monkeypatch.delenv("NERVOUS_LIVE_ENABLED", raising=False)
        monkeypatch.delenv("REDIS_URL", raising=False)
        src = open("agents/trading/executioner/agent.py", encoding="utf-8").read()
        assert "NERVOUS_LIVE_ENABLED" in src and "KillSwitch" in src
        # الحارس يأتي قبل فحص risk_decision
        assert src.index("KillSwitch()") < src.index("if not risk_decision.approved")
