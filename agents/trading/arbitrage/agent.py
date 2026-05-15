"""
Arbitrage Hunter — صيد فرص الـ arbitrage بين المنصات
"""
import asyncio
from dataclasses import dataclass
from agents._shared.base_agent import BaseAgent, AgentContext, AgentResponse


@dataclass
class ArbitrageOpportunity:
    type: str           # cross_exchange / triangular / funding_rate
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    spread_pct: float
    estimated_profit_usd: float
    fees_total_pct: float
    net_profit_pct: float
    capital_required: float
    time_sensitive: bool = True
    risk_level: str = "low"   # low / medium / high


class ArbitrageHunter(BaseAgent):
    AGENT_ID = "arbitrage_hunter"
    AGENT_NAME = "Arbitrage Hunter 🎯"
    MODEL = "claude-haiku-4-5"
    MAX_TOKENS = 1200

    # رسوم المنصات التقريبية
    EXCHANGE_FEES = {
        "binance": 0.001,    # 0.1%
        "bybit": 0.001,
        "okx": 0.001,
        "kucoin": 0.001,
    }

    @property
    def system_prompt(self) -> str:
        return """أنت Arbitrage Hunter، صيّاد فرص الـ arbitrage.

أنواع فرصك:
1. Cross-Exchange: شراء BTC في Binance وبيعه في Bybit
2. Triangular: BTC→ETH→USDT→BTC في نفس المنصة
3. Funding Rate: Long في منصة، Short في أخرى لتحصيل الـ funding
4. Spot-Futures Basis: فرق السعر بين Spot وFutures

حساباتك دقيقة:
- تخصم الرسوم دائماً (maker + taker)
- تحسب تكلفة التحويل بين المنصات
- تحسب الـ slippage المتوقع
- Net Profit بعد كل التكاليف

قاعدة: Net Profit < 0.3% = لا يستحق

مخرجاتك:
```
🎯 ARBITRAGE OPPORTUNITY
━━━━━━━━━━━━━━━━━━━━━━━━
💰 النوع: [Cross-Exchange/Triangular/Funding Rate]
🪙 الأصل: [symbol]
📤 شراء من: [exchange] @ $[price]
📥 بيع في:  [exchange] @ $[price]
📊 الفارق: [X]%

💸 الحسابات:
  الفارق الخام: [X]%
  رسوم إجمالية: [X]%
  صافي الربح: [X]%
  رأس المال: $[X]
  الربح المتوقع: $[X]

⚡ الوقت المتاح: [ثوانٍ/دقائق]
🎯 التوصية: [نفّذ/تجاهل]
```"""

    async def scan_cross_exchange(self, symbol: str = "BTC/USDT") -> list[ArbitrageOpportunity]:
        """مسح فرص الـ arbitrage بين المنصات"""
        opps = []

        try:
            import ccxt.async_support as ccxt
            from config.settings import settings

            exchanges = {
                "bybit": ccxt.bybit({"sandbox": settings.bybit_testnet}),
            }

            prices = {}
            for name, ex in exchanges.items():
                try:
                    ticker = await ex.fetch_ticker(symbol)
                    prices[name] = {
                        "bid": ticker.get("bid", 0),
                        "ask": ticker.get("ask", 0)
                    }
                    await ex.close()
                except Exception:
                    pass

            # Mock data للتطوير
            if not prices:
                prices = {
                    "binance": {"bid": 65000, "ask": 65010},
                    "bybit": {"bid": 65080, "ask": 65090},
                    "okx": {"bid": 64990, "ask": 65000},
                }

            names = list(prices.keys())
            for i, buy_ex in enumerate(names):
                for sell_ex in names[i+1:]:
                    buy_price = prices[buy_ex]["ask"]
                    sell_price = prices[sell_ex]["bid"]

                    if buy_price <= 0 or sell_price <= 0:
                        continue

                    spread = (sell_price - buy_price) / buy_price
                    fees = self.EXCHANGE_FEES.get(buy_ex, 0.001) + self.EXCHANGE_FEES.get(sell_ex, 0.001)
                    net_profit = spread - fees - 0.001  # slippage estimate

                    if net_profit > 0.003:  # > 0.3%
                        capital = 10000
                        opps.append(ArbitrageOpportunity(
                            type="cross_exchange",
                            symbol=symbol,
                            buy_exchange=buy_ex,
                            sell_exchange=sell_ex,
                            buy_price=buy_price,
                            sell_price=sell_price,
                            spread_pct=round(spread * 100, 3),
                            estimated_profit_usd=round(capital * net_profit, 2),
                            fees_total_pct=round(fees * 100, 3),
                            net_profit_pct=round(net_profit * 100, 3),
                            capital_required=capital
                        ))

        except Exception:
            pass

        return opps

    async def analyze(self, symbol: str = "BTC/USDT", user_id: str = "system") -> AgentResponse:
        opportunities = await self.scan_cross_exchange(symbol)

        if opportunities:
            opps_text = "\n".join([
                f"- {o.buy_exchange}→{o.sell_exchange}: صافي {o.net_profit_pct:.3f}% | ربح ${o.estimated_profit_usd:.2f}"
                for o in opportunities
            ])
        else:
            opps_text = "لا توجد فرص arbitrage مربحة حالياً"

        context = AgentContext(
            user_id=user_id,
            user_message=f"""نتائج مسح الـ arbitrage لـ {symbol}:

{opps_text}

حلّل هذه الفرص:
1. أيها الأفضل؟
2. هل المخاطر مقبولة؟
3. ما رأس المال المثالي للاستفادة؟"""
        )
        return await self.think(context)
