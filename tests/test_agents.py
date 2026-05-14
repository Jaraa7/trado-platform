"""
TRADO Tests — اختبارات الوحدة للـ agents
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


# ── Risk Guardian Tests ───────────────────────────────────────────────────────

class TestRiskGuardian:

    def setup_method(self):
        from agents.trading.risk_guardian.agent import RiskGuardian, TradeProposal
        self.guardian = RiskGuardian.__new__(RiskGuardian)
        self.guardian.user_id = "test"
        self.guardian.AGENT_ID = "risk_guardian"
        self.guardian.MAX_RISK_PER_TRADE = 0.02
        self.guardian.MAX_DAILY_LOSS = 0.06
        self.guardian.MAX_DRAWDOWN = 0.15
        self.guardian.MAX_LEVERAGE = 3
        self.guardian.MIN_RISK_REWARD = 1.5
        self.TradeProposal = TradeProposal

    def test_valid_trade_approved(self):
        proposal = self.TradeProposal(
            symbol="BTC/USDT",
            direction="long",
            entry_price=50000,
            stop_loss=48500,   # -3%
            take_profit=53000, # +6% → R:R = 2:1
            account_balance=10000,
            leverage=1
        )
        decision = self.guardian.calculate_position_size(proposal)
        assert decision.approved is True
        assert decision.risk_reward >= 1.5

    def test_bad_rr_rejected(self):
        proposal = self.TradeProposal(
            symbol="ETH/USDT",
            direction="long",
            entry_price=3000,
            stop_loss=2940,    # -2%
            take_profit=3015,  # +0.5% → R:R = 0.25:1
            account_balance=10000,
            leverage=1
        )
        decision = self.guardian.calculate_position_size(proposal)
        assert decision.approved is False
        assert decision.veto_applied is True

    def test_high_leverage_rejected(self):
        proposal = self.TradeProposal(
            symbol="BTC/USDT",
            direction="long",
            entry_price=50000,
            stop_loss=48000,
            take_profit=56000,
            account_balance=10000,
            leverage=10   # تجاوز الحد
        )
        decision = self.guardian.calculate_position_size(proposal)
        assert decision.approved is False

    def test_position_size_calculation(self):
        proposal = self.TradeProposal(
            symbol="BTC/USDT",
            direction="long",
            entry_price=50000,
            stop_loss=49000,   # -2%
            take_profit=53000, # +6%
            account_balance=10000,
            leverage=1
        )
        decision = self.guardian.calculate_position_size(proposal)
        if decision.approved:
            # Max risk = 2% of 10000 = $200
            # SL distance = 2%
            # Size = $200 / 0.02 = $10000 (أو أقل)
            assert decision.recommended_size > 0
            assert decision.risk_percentage == pytest.approx(2.0, abs=0.1)


# ── Memory System Tests ───────────────────────────────────────────────────────

class TestMemorySystem:

    @pytest.mark.asyncio
    async def test_remember_and_recall(self):
        from agents._shared.memory import MemorySystem, InMemoryStore

        memory = MemorySystem("test_agent", "test_user")
        memory._redis = InMemoryStore()

        await memory.remember("test_key", {"value": 42})
        result = await memory.recall("test_key")

        assert result is not None
        assert result["value"] == 42

    @pytest.mark.asyncio
    async def test_forget(self):
        from agents._shared.memory import MemorySystem, InMemoryStore

        memory = MemorySystem("test_agent", "test_user")
        memory._redis = InMemoryStore()

        await memory.remember("temp_key", "hello")
        await memory.forget("temp_key")
        result = await memory.recall("temp_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_missing_key_returns_none(self):
        from agents._shared.memory import MemorySystem, InMemoryStore

        memory = MemorySystem("test_agent", "test_user")
        memory._redis = InMemoryStore()

        result = await memory.recall("nonexistent_key")
        assert result is None


# ── Collaboration Rules Tests ─────────────────────────────────────────────────

class TestCollaborationRules:

    def test_executor_must_consult_risk(self):
        from agents._shared.collaboration import CollaborationRules

        consultations = CollaborationRules.should_consult(
            "executioner_pro", "execute_trade", confidence=0.5
        )
        assert "risk_guardian" in consultations

    def test_risk_guardian_has_veto(self):
        from agents._shared.collaboration import CollaborationRules

        assert CollaborationRules.can_veto("risk_guardian") is True
        assert CollaborationRules.can_veto("scanner_pro") is False


# ── Integration Test ──────────────────────────────────────────────────────────

class TestPipelineIntegration:

    @pytest.mark.asyncio
    async def test_risk_pipeline(self):
        """اختبار pipeline مبسّط بدون APIs خارجية"""
        from agents.trading.risk_guardian.agent import RiskGuardian, TradeProposal

        guardian = RiskGuardian.__new__(RiskGuardian)
        guardian.user_id = "test"
        guardian.AGENT_ID = "risk_guardian"
        guardian.MAX_RISK_PER_TRADE = 0.02
        guardian.MAX_DAILY_LOSS = 0.06
        guardian.MAX_DRAWDOWN = 0.15
        guardian.MAX_LEVERAGE = 3
        guardian.MIN_RISK_REWARD = 1.5

        proposal = TradeProposal(
            symbol="BTC/USDT",
            direction="long",
            entry_price=50000,
            stop_loss=48500,
            take_profit=53000,
            account_balance=10000,
            leverage=1
        )

        decision = guardian.calculate_position_size(proposal)
        assert decision is not None
        assert isinstance(decision.approved, bool)
