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


# ── New Agents Tests ──────────────────────────────────────────────────────────

class TestRegimeDetector:

    def setup_method(self):
        from agents.trading.regime_detector.agent import RegimeDetector
        self.detector = RegimeDetector.__new__(RegimeDetector)
        self.detector.user_id = "test"

    def _make_ohlcv(self, n=30, trend="up"):
        import random
        candles = []
        price = 50000
        for i in range(n):
            if trend == "up":
                price *= (1 + random.uniform(0, 0.005))
            elif trend == "down":
                price *= (1 - random.uniform(0, 0.005))
            candles.append([i, price*0.99, price*1.01, price*0.98, price, price*100])
        return candles

    def test_bull_regime(self):
        from agents.trading.regime_detector.agent import MarketRegime
        ohlcv = self._make_ohlcv(30, "up")
        result = self.detector.quick_regime(ohlcv, adx=35)
        assert result.regime in [MarketRegime.BULL_STRONG, MarketRegime.BULL_WEAK]
        assert result.confidence > 0.5

    def test_bear_regime(self):
        from agents.trading.regime_detector.agent import MarketRegime
        ohlcv = self._make_ohlcv(30, "down")
        result = self.detector.quick_regime(ohlcv, adx=35)
        assert result.regime in [MarketRegime.BEAR_STRONG, MarketRegime.BEAR_WEAK]

    def test_empty_data_fallback(self):
        from agents.trading.regime_detector.agent import MarketRegime
        result = self.detector.quick_regime([])
        assert result.regime == MarketRegime.SIDEWAYS


class TestSentimentAnalyzer:

    def setup_method(self):
        from agents.trading.sentiment.agent import SentimentAnalyzer
        self.analyzer = SentimentAnalyzer.__new__(SentimentAnalyzer)

    def test_extreme_fear_is_buy(self):
        result = self.analyzer.interpret_score(15)
        assert result.label == "Extreme Fear"
        assert result.contrarian_signal == "buy"

    def test_extreme_greed_is_sell(self):
        result = self.analyzer.interpret_score(90)
        assert result.label == "Extreme Greed"
        assert result.contrarian_signal == "sell"

    def test_neutral_is_hold(self):
        result = self.analyzer.interpret_score(50)
        assert result.contrarian_signal == "hold"


class TestPortfolioManager:

    def setup_method(self):
        from agents.trading.portfolio.agent import PortfolioManager
        self.manager = PortfolioManager.__new__(PortfolioManager)

    def test_allocation_sums_to_100(self):
        alloc = self.manager.get_regime_allocation("bull_strong", 10000)
        total = sum(v["pct"] for v in alloc.values())
        assert total == 100

    def test_bear_has_high_cash(self):
        alloc = self.manager.get_regime_allocation("bear_strong", 10000)
        assert alloc["cash"]["pct"] >= 80

    def test_bull_has_low_cash(self):
        alloc = self.manager.get_regime_allocation("bull_strong", 10000)
        assert alloc["cash"]["pct"] <= 15


class TestBacktester:

    @pytest.mark.asyncio
    async def test_simple_backtest(self):
        from agents.trading.backtester.agent import BacktesterPro

        tester = BacktesterPro.__new__(BacktesterPro)
        tester.user_id = "test"

        # بيانات صناعية
        import random
        price = 50000
        ohlcv = []
        for i in range(100):
            price += random.uniform(-500, 500)
            ohlcv.append([i, price-100, price+200, price-200, price, 1000])

        # استراتيجية بسيطة
        def entry(candles):
            if len(candles) < 5:
                return False
            return candles[-1][4] > candles[-5][4]

        def exit_sig(candles):
            if len(candles) < 3:
                return False
            return candles[-1][4] < candles[-3][4]

        result = await tester.run_simple_backtest(ohlcv, entry, exit_sig)
        assert result.total_trades >= 0
