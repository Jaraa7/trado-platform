"""
Executioner Pro — تنفيذ الصفقات بأسرع وأذكى طريقة
"""
import asyncio
import time
from dataclasses import dataclass
from typing import Optional
from loguru import logger
from agents._shared.base_agent import BaseAgent, AgentContext, AgentResponse
from agents.trading.risk_guardian.agent import TradeProposal, RiskDecision


@dataclass
class ExecutionResult:
    success: bool
    order_id: Optional[str] = None
    symbol: str = ""
    side: str = ""
    price: float = 0.0
    amount: float = 0.0
    slippage: float = 0.0
    execution_time_ms: float = 0.0
    error: Optional[str] = None
    exchange: str = ""


class ExecutionerPro(BaseAgent):
    AGENT_ID = "executioner_pro"
    AGENT_NAME = "Executioner Pro ⚡"
    MODEL = "claude-haiku-4-5"
    MAX_TOKENS = 500

    @property
    def system_prompt(self) -> str:
        return """أنت Executioner Pro، متخصص تنفيذ صفقات.
هدفك: تنفيذ الأوامر بأقل slippage وأسرع وقت (<100ms).
تُبلّغ دائماً بـ: رقم الطلب، السعر الفعلي، الـ slippage."""

    async def execute_order(
        self,
        proposal: TradeProposal,
        risk_decision: RiskDecision,
        user_id: str = "system",
        testnet: bool = True
    ) -> ExecutionResult:
        """تنفيذ الصفقة على المنصة"""

        if not risk_decision.approved:
            return ExecutionResult(
                success=False,
                symbol=proposal.symbol,
                error=f"Risk Guardian رفض: {risk_decision.reason}"
            )

        start = time.time()

        try:
            import ccxt.async_support as ccxt
            from config.settings import settings

            exchange = ccxt.bybit({
                "sandbox": testnet,
                "apiKey": settings.bybit_api_key,
                "secret": settings.bybit_secret,
                "options": {"defaultType": "spot"}
            })

            await exchange.load_markets()

            side = "buy" if proposal.direction == "long" else "sell"
            amount = risk_decision.recommended_size / proposal.entry_price

            # تنفيذ الأمر
            order = await exchange.create_order(
                symbol=proposal.symbol,
                type="limit",
                side=side,
                amount=round(amount, 6),
                price=proposal.entry_price,
                params={"timeInForce": "GTC"}
            )

            # حساب الـ slippage
            filled_price = order.get("average") or order.get("price") or proposal.entry_price
            slippage = abs(filled_price - proposal.entry_price) / proposal.entry_price * 100

            execution_time = (time.time() - start) * 1000

            await exchange.close()

            logger.info(
                f"⚡ Order executed: {proposal.symbol} {side} "
                f"| price={filled_price} | slippage={slippage:.3f}% "
                f"| time={execution_time:.0f}ms"
            )

            return ExecutionResult(
                success=True,
                order_id=order.get("id"),
                symbol=proposal.symbol,
                side=side,
                price=filled_price,
                amount=amount,
                slippage=slippage,
                execution_time_ms=execution_time,
                exchange="bybit"
            )

        except Exception as e:
            execution_time = (time.time() - start) * 1000
            logger.error(f"❌ Execution error: {e}")
            return ExecutionResult(
                success=False,
                symbol=proposal.symbol,
                error=str(e),
                execution_time_ms=execution_time
            )

    async def place_stop_and_tp(
        self,
        symbol: str,
        stop_price: float,
        tp_price: float,
        amount: float,
        side: str = "buy",
        testnet: bool = True
    ) -> dict:
        """وضع Stop Loss و Take Profit"""
        try:
            import ccxt.async_support as ccxt
            from config.settings import settings

            exchange = ccxt.bybit({
                "sandbox": testnet,
                "apiKey": settings.bybit_api_key,
                "secret": settings.bybit_secret,
            })

            close_side = "sell" if side == "buy" else "buy"

            # Stop Loss
            sl_order = await exchange.create_order(
                symbol=symbol,
                type="stop_market",
                side=close_side,
                amount=amount,
                params={"stopPrice": stop_price, "reduceOnly": True}
            )

            # Take Profit
            tp_order = await exchange.create_order(
                symbol=symbol,
                type="limit",
                side=close_side,
                amount=amount,
                price=tp_price,
                params={"reduceOnly": True}
            )

            await exchange.close()

            return {
                "sl_order_id": sl_order.get("id"),
                "tp_order_id": tp_order.get("id"),
                "success": True
            }

        except Exception as e:
            logger.error(f"SL/TP placement error: {e}")
            return {"success": False, "error": str(e)}
