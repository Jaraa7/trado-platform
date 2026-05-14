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
from agents._shared.collaboration import CollaborationRules, Priority
from agents.trading.scanner.agent import ScannerPro
from agents.trading.analyst.agent import AnalystMaster
from agents.trading.risk_guardian.agent import RiskGuardian, TradeProposal
from agents.trading.executioner.agent import ExecutionerPro
from agents.trading.observatory.agent import Observatory


@dataclass
class TradingSignal:
    """إشارة تداول كاملة من الـ pipeline"""
    symbol: str
    direction: str          # long | short
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float       # 0-1
    analyst_report: str = ""
    risk_decision: Any = None
    execution_result: Any = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class TRADOOrchestrator:
    """
    المخ المركزي لـ TRADO.
    
    Pipeline الكامل:
    Scanner → Analyst → Risk Guardian → Executioner → Observatory
    """

    def __init__(self, user_id: str = "system"):
        self.user_id = user_id
        self.scanner = ScannerPro(user_id)
        self.analyst = AnalystMaster(user_id)
        self.risk_guardian = RiskGuardian(user_id)
        self.executioner = ExecutionerPro(user_id)
        self.observatory = Observatory(user_id)

        self._signals_processed = 0
        self._signals_executed = 0
        self._signals_vetoed = 0

        logger.info(f"🧠 TRADO Orchestrator initialized for {user_id}")

    async def run_trading_pipeline(
        self,
        account_balance: float = 1000.0,
        auto_execute: bool = False,
        testnet: bool = True
    ) -> list[TradingSignal]:
        """
        تشغيل pipeline التداول الكامل
        """
        logger.info("🚀 Starting TRADO Trading Pipeline...")
        signals = []

        # ═══ الخطوة 1: Scanner ════════════════════════════════════
        logger.info("🔍 Step 1: Scanning markets...")
        scan_data = await self.scanner.scan_markets()

        if not scan_data.get("opportunities"):
            logger.info("📊 No opportunities found in scan")
            return signals

        logger.info(f"📊 Found {scan_data['found']} opportunities")

        # ═══ الخطوة 2: Analysis لأفضل 3 فرص ══════════════════════
        top_opportunities = scan_data["opportunities"][:3]

        for opp in top_opportunities:
            symbol = opp["symbol"]
            self._signals_processed += 1

            logger.info(f"📊 Step 2: Analyzing {symbol}...")

            # تحليل مبسّط كمثال
            market_data = {
                "symbol": symbol,
                "price": opp.get("price", 0),
                "volume_ratio": opp.get("volume_ratio", 1),
                "change_24h": opp.get("change_24h", 0),
                "note": "Scanner detected high volume activity"
            }

            analyst_response = await self.analyst.analyze(symbol, market_data, self.user_id)

            if not analyst_response.success:
                continue

            # تحقق من جودة الـ Setup (A أو A+)
            if "Setup Quality: C" in analyst_response.content or \
               "Setup Quality: B" in analyst_response.content.replace("B+", ""):
                logger.info(f"⏭️ {symbol}: Setup quality too low, skipping")
                continue

            # ═══ الخطوة 3: Risk Guardian ══════════════════════════
            logger.info(f"🛡️ Step 3: Risk assessment for {symbol}...")

            # استخرج النقاط من تحليل الـ Analyst (مبسّط)
            entry_price = opp.get("price", 100)
            stop_loss = entry_price * 0.97    # -3%
            take_profit = entry_price * 1.06  # +6%

            proposal = TradeProposal(
                symbol=symbol,
                direction="long",
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                account_balance=account_balance,
                leverage=1
            )

            risk_decision = self.risk_guardian.calculate_position_size(proposal)

            if not risk_decision.approved:
                self._signals_vetoed += 1
                logger.info(f"🚫 {symbol}: Risk Guardian VETO — {risk_decision.reason}")
                continue

            signal = TradingSignal(
                symbol=symbol,
                direction="long",
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                confidence=0.75,
                analyst_report=analyst_response.content,
                risk_decision=risk_decision
            )

            # ═══ الخطوة 4: Execute (إذا auto_execute) ═══════════
            if auto_execute:
                logger.info(f"⚡ Step 4: Executing {symbol}...")
                execution = await self.executioner.execute_order(
                    proposal, risk_decision, self.user_id, testnet
                )
                signal.execution_result = execution

                if execution.success:
                    self._signals_executed += 1
                    await self.observatory.update_position(
                        symbol, entry_price, entry_price, risk_decision.recommended_size, "long"
                    )

            signals.append(signal)

        logger.info(
            f"✅ Pipeline complete: {len(signals)} signals | "
            f"vetoed: {self._signals_vetoed} | executed: {self._signals_executed}"
        )
        return signals

    async def get_system_status(self) -> dict:
        """حالة النظام الكاملة"""
        return {
            "status": "running",
            "user_id": self.user_id,
            "signals_processed": self._signals_processed,
            "signals_executed": self._signals_executed,
            "signals_vetoed": self._signals_vetoed,
            "agents": {
                "scanner": {"calls": self.scanner.call_count, "cost": f"${self.scanner.total_cost:.4f}"},
                "analyst": {"calls": self.analyst.call_count, "cost": f"${self.analyst.total_cost:.4f}"},
                "risk_guardian": {"calls": self.risk_guardian.call_count, "cost": f"${self.risk_guardian.total_cost:.4f}"},
                "executioner": {"calls": self.executioner.call_count, "cost": f"${self.executioner.total_cost:.4f}"},
                "observatory": {"calls": self.observatory.call_count, "cost": f"${self.observatory.total_cost:.4f}"},
            },
            "total_cost": f"${sum([
                self.scanner.total_cost,
                self.analyst.total_cost,
                self.risk_guardian.total_cost,
                self.executioner.total_cost,
                self.observatory.total_cost
            ]):.4f}",
            "timestamp": datetime.utcnow().isoformat()
        }
