"""
TRADO Orchestrator — المخ المركزي
ينسق بين الـ 87 agent ويتخذ القرارات النهائية
"""
import asyncio
from typing import Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger

from agents._shared.base_agent import AgentContext, AgentResponse
from agents.trading.scanner.agent import ScannerPro
from agents.trading.analyst.agent import AnalystMaster
from agents.trading.risk_guardian.agent import RiskGuardian, TradeProposal
from agents.trading.executioner.agent import ExecutionerPro
from agents.trading.observatory.agent import Observatory
from agents.trading.regime_detector.agent import RegimeDetector
from agents.trading.news_analyst.agent import NewsAnalyst
from agents.trading.sentiment.agent import SentimentAnalyzer
from agents.trading.whale_tracker.agent import WhaleTracker
from agents.trading.macro.agent import MacroEconomist
from agents.trading.strategy.agent import StrategyDesigner
from agents.trading.portfolio.agent import PortfolioManager, PortfolioState
from agents.trading.pattern.agent import PatternRecognition
from agents.trading.backtester.agent import BacktesterPro
from agents.trading.arbitrage.agent import ArbitrageHunter


@dataclass
class TradingSignal:
    symbol: str
    direction: str
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float
    analyst_report: str = ""
    risk_decision: Any = None
    execution_result: Any = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class TRADOOrchestrator:
    """
    المخ المركزي لـ TRADO.
    يملك جميع الـ 15 trading agent ويشغّلها بتنسيق.

    Pipeline الكامل:
    Context Gathering → Scanner → Regime → Analyst → Risk → Execute → Monitor
    """

    def __init__(self, user_id: str = "system"):
        self.user_id = user_id

        # ── Trading Intelligence (15 agents) ──────────────────────────
        self.scanner         = ScannerPro(user_id)
        self.analyst         = AnalystMaster(user_id)
        self.risk_guardian   = RiskGuardian(user_id)
        self.executioner     = ExecutionerPro(user_id)
        self.observatory     = Observatory(user_id)
        self.regime_detector = RegimeDetector(user_id)
        self.news_analyst    = NewsAnalyst(user_id)
        self.sentiment       = SentimentAnalyzer(user_id)
        self.whale_tracker   = WhaleTracker(user_id)
        self.macro           = MacroEconomist(user_id)
        self.strategy        = StrategyDesigner(user_id)
        self.portfolio       = PortfolioManager(user_id)
        self.pattern         = PatternRecognition(user_id)
        self.backtester      = BacktesterPro(user_id)
        self.arbitrage       = ArbitrageHunter(user_id)

        self._all_agents = [
            self.scanner, self.analyst, self.risk_guardian,
            self.executioner, self.observatory, self.regime_detector,
            self.news_analyst, self.sentiment, self.whale_tracker,
            self.macro, self.strategy, self.portfolio,
            self.pattern, self.backtester, self.arbitrage
        ]

        self._signals_processed = 0
        self._signals_executed  = 0
        self._signals_vetoed    = 0

        logger.info(f"🧠 TRADO Orchestrator v2 initialized — 15 trading agents ready | user={user_id}")

    async def gather_market_context(self) -> dict:
        """
        الخطوة 0: جمع السياق الكامل للسوق بشكل متوازٍ
        News + Sentiment + Whale + Macro في نفس الوقت
        """
        logger.info("📡 Gathering market context...")

        results = await asyncio.gather(
            self.news_analyst.analyze_news(self.user_id),
            self.sentiment.analyze("BTC", self.user_id),
            self.whale_tracker.analyze(self.user_id),
            return_exceptions=True
        )

        context = {}
        for i, (key, result) in enumerate(zip(["news", "sentiment", "whale"], results)):
            if isinstance(result, AgentResponse) and result.success:
                context[key] = result.content[:300]
            else:
                context[key] = "unavailable"

        logger.info(f"✅ Context gathered: {list(context.keys())}")
        return context

    async def run_trading_pipeline(
        self,
        account_balance: float = 1000.0,
        auto_execute: bool = False,
        testnet: bool = True
    ) -> list[TradingSignal]:
        """Pipeline التداول الكامل"""
        logger.info("🚀 Starting TRADO Trading Pipeline v2...")
        signals = []

        # ═══ الخطوة 0: Context ═══════════════════════════════════════
        market_context = await self.gather_market_context()

        # ═══ الخطوة 1: Scanner ═══════════════════════════════════════
        logger.info("🔍 Scanning markets...")
        scan_data = await self.scanner.scan_markets()

        if not scan_data.get("opportunities"):
            logger.info("📊 No opportunities found")
            return signals

        # ═══ الخطوة 2: Arbitrage (بالتوازي مع الـ scan) ═════════════
        arb_task = asyncio.create_task(self.arbitrage.analyze("BTC/USDT", self.user_id))

        # ═══ الخطوة 3: Regime Detection ══════════════════════════════
        regime_response = await self.regime_detector.analyze(
            {"price_change": 2.5, "adx": 28}, self.user_id
        )
        current_regime = "bull_weak"  # fallback

        # ═══ الخطوة 4: Strategy for Regime ══════════════════════════
        strategy_response = await self.strategy.design_for_regime(
            current_regime, "BTC/USDT", account_balance, self.user_id
        )

        # ═══ الخطوة 5: Analyze top opportunities ════════════════════
        for opp in scan_data["opportunities"][:3]:
            symbol = opp["symbol"]
            self._signals_processed += 1

            logger.info(f"📊 Analyzing {symbol}...")

            market_data = {
                "symbol": symbol,
                "price": opp.get("price", 0),
                "volume_ratio": opp.get("volume_ratio", 1),
                "change_24h": opp.get("change_24h", 0),
                "regime": current_regime,
                "context_summary": str(market_context)[:200]
            }

            analyst_response = await self.analyst.analyze(symbol, market_data, self.user_id)
            if not analyst_response.success:
                continue

            # ═══ الخطوة 6: Risk Check ═════════════════════════════
            entry_price = opp.get("price", 100)
            proposal = TradeProposal(
                symbol=symbol,
                direction="long",
                entry_price=entry_price,
                stop_loss=entry_price * 0.97,
                take_profit=entry_price * 1.06,
                account_balance=account_balance,
                leverage=1
            )

            risk_decision = self.risk_guardian.calculate_position_size(proposal)

            if not risk_decision.approved:
                self._signals_vetoed += 1
                logger.info(f"🚫 {symbol}: VETO — {risk_decision.reason}")
                continue

            signal = TradingSignal(
                symbol=symbol,
                direction="long",
                entry_price=entry_price,
                stop_loss=entry_price * 0.97,
                take_profit=entry_price * 1.06,
                confidence=0.75,
                analyst_report=analyst_response.content,
                risk_decision=risk_decision
            )

            # ═══ الخطوة 7: Execute ════════════════════════════════
            if auto_execute:
                execution = await self.executioner.execute_order(
                    proposal, risk_decision, self.user_id, testnet
                )
                signal.execution_result = execution
                if execution.success:
                    self._signals_executed += 1
                    await self.observatory.update_position(
                        symbol, entry_price, entry_price,
                        risk_decision.recommended_size, "long"
                    )

            signals.append(signal)

        # انتظار نتيجة الـ arbitrage
        try:
            arb_result = await asyncio.wait_for(arb_task, timeout=10)
            logger.info(f"🎯 Arbitrage scan complete")
        except asyncio.TimeoutError:
            pass

        logger.info(
            f"✅ Pipeline complete | signals={len(signals)} | "
            f"vetoed={self._signals_vetoed} | executed={self._signals_executed}"
        )
        return signals

    async def get_full_market_analysis(self, user_id: str = "system") -> dict:
        """تحليل شامل للسوق من كل الـ agents"""
        results = {}

        tasks = {
            "regime": self.regime_detector.analyze({}, user_id),
            "news": self.news_analyst.analyze_news(user_id),
            "sentiment": self.sentiment.analyze("BTC", user_id),
            "whale": self.whale_tracker.analyze(user_id),
            "macro": self.macro.analyze_macro(user_id),
        }

        for name, task in tasks.items():
            try:
                response = await asyncio.wait_for(task, timeout=15)
                results[name] = response.content[:500] if response.success else "error"
            except Exception as e:
                results[name] = f"timeout/error: {str(e)[:50]}"

        return results

    async def get_system_status(self) -> dict:
        return {
            "status": "running",
            "user_id": self.user_id,
            "trading_agents": 15,
            "total_agents": 87,
            "signals_processed": self._signals_processed,
            "signals_executed": self._signals_executed,
            "signals_vetoed": self._signals_vetoed,
            "agents_cost": {
                agent.AGENT_NAME: f"${agent.total_cost:.4f}"
                for agent in self._all_agents
            },
            "total_cost": f"${sum(a.total_cost for a in self._all_agents):.4f}",
            "timestamp": datetime.utcnow().isoformat()
        }
