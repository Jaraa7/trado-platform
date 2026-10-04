"""اختبارات الطبقة العصبية — كلها بلا شبكة."""
import math
import pytest

from nervous.goals import GoalEngine, Goal, TIER_TOP, TIER_IMPORTANT, TIER_LATER
from nervous.market import ema, atr, realized_volatility, classify_regime, rank_movers, recommend_posture
from nervous.performance import evaluate_outcome, compute_stats, PerformanceTracker, MIN_SAMPLE
from nervous.conflicts import ConflictChecker


# ── Goals ────────────────────────────────────────────────────────────
class TestGoals:
    def _engine(self, tmp_path):
        return GoalEngine(str(tmp_path / "goals.json"))

    def test_score_formula(self):
        g = Goal("a", "x", impact=10, urgency=10, effort=1, confidence=10)
        assert g.score == 10.0
        g2 = Goal("b", "y", impact=10, urgency=10, effort=10, confidence=10)
        assert g2.score == 1.0

    def test_clamp_and_self_dependency(self):
        g = Goal("a", "x", impact=50, urgency=0, effort=-3)
        assert (g.impact, g.urgency, g.effort) == (10, 1, 1)
        with pytest.raises(ValueError):
            Goal("a", "x", 5, 5, 5, depends_on=["a"])

    def test_dependency_order_beats_score(self, tmp_path):
        e = self._engine(tmp_path)
        e.add(Goal("base", "أساس", impact=3, urgency=3, effort=5))
        e.add(Goal("big", "كبير", impact=10, urgency=10, effort=1, depends_on=["base"]))
        order = [g.id for g in e.ranked()]
        assert order == ["base", "big"]

    def test_cycle_rejected(self, tmp_path):
        e = self._engine(tmp_path)
        e.add(Goal("a", "a", 5, 5, 5))
        e.add(Goal("b", "b", 5, 5, 5, depends_on=["a"]))
        with pytest.raises(ValueError):
            e.update("a", depends_on=["b"])

    def test_tiers_and_persistence(self, tmp_path):
        e = self._engine(tmp_path)
        for i in range(10):
            e.add(Goal(f"g{i}", f"هدف {i}", impact=10 - i, urgency=10 - i, effort=1 + i * 0.5))
        t = e.tiers()
        assert len(t[TIER_TOP]) == 2 and len(t[TIER_IMPORTANT]) == 3 and len(t[TIER_LATER]) == 5
        assert t[TIER_TOP][0].id == "g0"
        e.update("g0", status="done"); e.save()
        e2 = GoalEngine(str(tmp_path / "goals.json"))
        assert e2.next_action().id == "g1"
        assert "الأهم" in e2.report()


# ── Market ───────────────────────────────────────────────────────────
def _candles(prices, spread=0.01):
    return [{"ts": i, "open": p, "high": p * (1 + spread), "low": p * (1 - spread), "close": p, "volume": 1}
            for i, p in enumerate(prices)]


class TestMarket:
    def test_ema_atr(self):
        assert ema([1, 1, 1, 1], 3) == [1, 1, 1, 1]
        c = _candles([100] * 20)
        assert math.isclose(atr(c), 2.0, rel_tol=1e-6)

    def test_regime_trending_up(self):
        c = _candles([100 * (1.004 ** i) for i in range(120)])
        r = classify_regime(c)
        assert r["regime"] == "trending_up" and r["ema_bias"] == "up" and r["adx"] > 25

    def test_regime_ranging(self):
        c = _candles([100 + (i % 2) * 0.5 for i in range(120)], spread=0.002)
        assert classify_regime(c)["regime"] == "ranging"

    def test_regime_volatile_and_unknown(self):
        c = _candles([100 + (i % 2) * 20 for i in range(120)], spread=0.06)
        assert classify_regime(c)["regime"] == "volatile"
        assert classify_regime(_candles([1, 2, 3]))["regime"] == "unknown"

    def test_volatility_and_movers(self):
        assert realized_volatility(_candles([100] * 30)) == 0
        assert realized_volatility(_candles([100, 110, 100, 110, 100] * 6)) > 5
        m = rank_movers([{"symbol": "A", "price": 1, "change_24h": 5},
                         {"symbol": "B", "price": 1, "change_24h": -3},
                         {"symbol": "C", "price": 1, "change_24h": 1}], top=1)
        assert m["gainers"][0]["symbol"] == "A" and m["losers"][0]["symbol"] == "B"
        assert m["breadth_pct_up"] == pytest.approx(66.7)

    def test_posture_rules(self):
        p = recommend_posture({"regime": "trending_up"}, 50, 70)
        assert "trend_following" in p["favor"] and p["size_multiplier"] == 1.0
        p = recommend_posture({"regime": "volatile"}, 90, 50)
        assert p["size_multiplier"] == 0.5
        p = recommend_posture({"regime": "ranging"}, 50, 50)
        assert "mean_reversion" in p["favor"]


# ── Performance ──────────────────────────────────────────────────────
class TestPerformance:
    sig_long = {"direction": "long", "entry_price": 100, "stop_loss": 95, "take_profit_1": 110}
    sig_short = {"direction": "short", "entry_price": 100, "stop_loss": 105, "take_profit_1": 90}

    def test_outcomes(self):
        tp = [{"high": 111, "low": 99, "close": 110}]
        sl = [{"high": 101, "low": 94, "close": 96}]
        both = [{"high": 111, "low": 94, "close": 100}]
        assert evaluate_outcome(self.sig_long, tp) == {"status": "hit_tp", "r_multiple": 2.0, "bars": 1}
        assert evaluate_outcome(self.sig_long, sl)["status"] == "hit_sl"
        assert evaluate_outcome(self.sig_long, both)["status"] == "hit_sl"  # محافظ
        assert evaluate_outcome(self.sig_short, [{"high": 101, "low": 89, "close": 90}])["r_multiple"] == 2.0
        exp = evaluate_outcome(self.sig_long, [{"high": 103, "low": 98, "close": 102.5}])
        assert exp["status"] == "expired" and exp["r_multiple"] == 0.5
        assert evaluate_outcome(self.sig_long, [])["status"] == "active"
        assert evaluate_outcome({"direction": "long", "entry_price": 1, "stop_loss": 1}, tp)["status"] == "invalid"

    def test_stats(self):
        s = compute_stats([{"status": "hit_tp", "r_multiple": 2}, {"status": "hit_sl", "r_multiple": -1},
                           {"status": "hit_sl", "r_multiple": -1}, {"status": "active", "r_multiple": 0}])
        assert s["n"] == 3 and s["win_rate"] == pytest.approx(33.3)
        assert s["expectancy_r"] == 0 and s["profit_factor"] == 1.0 and s["max_drawdown_r"] == 2.0

    def _rows(self, agent, n, r):
        return [{"generated_by": agent, "symbol": "BTC/USDT", "status": "hit_tp" if r > 0 else "hit_sl",
                 "r_multiple": r} for _ in range(n)]

    def test_recommendations_observe_when_small(self):
        t = PerformanceTracker(self._rows("a", MIN_SAMPLE - 1, 1))
        assert t.recommendations()[0]["action"] == "observe"

    def test_recommendations_levels(self):
        bad = self._rows("loser", 25, -1)
        good = self._rows("winner", 20, 2) + self._rows("winner", 5, -1)
        t = PerformanceTracker(bad + good)
        recs = {r["target"]: r for r in t.recommendations()}
        assert recs["loser"]["action"] == "pause_agent" and recs["loser"]["level"] == 1
        assert recs["winner"]["action"] == "promote_candidate" and recs["winner"]["level"] == 2
        assert set(t.report()) >= {"overall", "by_agent", "by_symbol", "recommendations"}


# ── Conflicts (على المستودع الحقيقي) ───────────────────────────────
class TestConflicts:
    def test_repo_has_no_conflicts(self):
        res = ConflictChecker().run()
        assert res["ok"], res["issues"]
        assert res["counts"]["agents"] >= 80
        assert "nervous_goals" in ConflictChecker().check_tables()


# ── Lifecycle + Router ───────────────────────────────────────────────
class TestLifecycleAndRouter:
    def test_every_lifecycle_entry_is_a_registered_agent(self):
        from agents.lifecycle import LIFECYCLE
        from agents.registry import AGENT_REGISTRY
        registered = {a for d in AGENT_REGISTRY.values() for a in d}
        unknown = set(LIFECYCLE) - registered
        assert not unknown, unknown
        for k, m in LIFECYCLE.items():
            if m.get("status") == "merged":
                assert m["into"] in registered, f"{k} → {m['into']} غير مسجل"

    def test_merged_resolves_and_parked_blocked(self):
        from agents.lifecycle import resolve_alias
        from agents.registry import get_agent
        assert resolve_alias("chatbot_free") == "support_pro"
        assert resolve_alias("test_engineer") == "bug_hunter"
        with pytest.raises(ValueError, match="parked"):
            get_agent("hr_team_manager")
        with pytest.raises(ValueError, match="removed"):
            get_agent("tax_compliance")

    def test_get_agent_sets_tier(self):
        from agents.registry import get_agent
        a = get_agent("chatbot_pro")           # مدمج → support_pro
        assert a.AGENT_ID == "support_pro" and a.TIER == "cheap"
        assert get_agent("analyst_master").TIER == "frontier"

    def test_router_primary_then_fallback(self):
        from core.llm_router import LLMRouter
        calls = []
        def caller(model, system, messages, mt):
            calls.append(model)
            if model.startswith("deepseek"):
                raise RuntimeError("down")
            return "ok", 100, 50
        r = LLMRouter(caller=caller, metrics_sink=lambda row: None)
        res = r.complete("standard", "sys", [{"role": "user", "content": "x"}], agent_id="t")
        assert calls == ["deepseek:deepseek-chat", "google:gemini-3.1-pro"]
        assert res.fallback_used and res.model == "google:gemini-3.1-pro"
        assert res.cost_usd == pytest.approx(100 / 1e6 * 2.0 + 50 / 1e6 * 12.0)

    def test_router_downgrade_on_budget(self):
        from core.llm_router import LLMRouter, BudgetExceeded
        # تجاوز دائم → ينزل frontier→standard→cheap ثم يرفع BudgetExceeded
        r = LLMRouter(caller=lambda m, s, msgs, mt: ("ok", 1, 1), metrics_sink=lambda row: None,
                      budget_check=lambda a: True)
        with pytest.raises(BudgetExceeded):
            r.complete("frontier", "s", [], agent_id="x")
        # لا تجاوز → الفئة كما هي
        r2 = LLMRouter(caller=lambda m, s, msgs, mt: ("ok", 1, 1), metrics_sink=lambda row: None,
                       budget_check=lambda a: False)
        assert r2.effective_tier("frontier", "y") == "frontier"

    def test_router_all_fail_raises(self):
        from core.llm_router import LLMRouter
        r = LLMRouter(caller=lambda *a: (_ for _ in ()).throw(RuntimeError("x")), metrics_sink=lambda row: None)
        with pytest.raises(RuntimeError, match="كل النماذج فشلت"):
            r.complete("cheap", "s", [])

    def test_no_hardcoded_model_names_outside_config(self):
        import re, pathlib
        root = pathlib.Path(__file__).resolve().parent.parent
        bad = []
        for f in root.rglob("*.py"):
            if any(p in f.parts for p in (".git", "tests")) or f.name == "models.py":
                continue
            if re.search(r'["\'](claude-[a-z0-9.-]+|gpt-[a-z0-9.-]+|gemini-[a-z0-9.-]+|deepseek-[a-z]+)["\']', f.read_text(encoding="utf-8")):
                bad.append(f.relative_to(root).as_posix())
        assert not bad, bad
