"""
Portfolio Manager — توزيع الأصول الذكي
"""
from dataclasses import dataclass, field
from agents._shared.base_agent import BaseAgent, AgentContext, AgentResponse


@dataclass
class PortfolioAsset:
    symbol: str
    allocation_pct: float   # % من المحفظة
    current_value: float
    entry_price: float = 0
    current_price: float = 0
    pnl_pct: float = 0

    @property
    def pnl_usd(self) -> float:
        return self.current_value * self.pnl_pct / 100


@dataclass
class PortfolioState:
    total_value: float
    assets: list[PortfolioAsset] = field(default_factory=list)
    cash_pct: float = 20.0      # 20% كاش افتراضياً
    stablecoin_pct: float = 10.0

    @property
    def crypto_pct(self) -> float:
        return 100 - self.cash_pct - self.stablecoin_pct


class PortfolioManager(BaseAgent):
    AGENT_ID = "portfolio_manager"
    AGENT_NAME = "Portfolio Manager 💼"
    MODEL = "claude-sonnet-4-5"
    MAX_TOKENS = 2500

    # توزيع الأصول الافتراضي حسب الـ regime
    REGIME_ALLOCATION = {
        "bull_strong":  {"BTC": 40, "ETH": 25, "alts": 25, "cash": 10},
        "bull_weak":    {"BTC": 35, "ETH": 20, "alts": 15, "cash": 30},
        "sideways":     {"BTC": 30, "ETH": 20, "alts": 10, "cash": 40},
        "bear_weak":    {"BTC": 20, "ETH": 10, "alts": 5, "cash": 65},
        "bear_strong":  {"BTC": 10, "ETH": 5, "alts": 0, "cash": 85},
        "volatile":     {"BTC": 20, "ETH": 10, "alts": 0, "cash": 70},
    }

    @property
    def system_prompt(self) -> str:
        return """أنت Portfolio Manager، خبير توزيع الأصول.

فلسفتك: لا تضع كل بيضك في سلة واحدة. الهدف: أقصى عائد بأقل مخاطرة.

تستخدم:
- Markowitz Mean-Variance Optimization
- Risk Parity (توزيع متساوٍ للمخاطر)
- Hierarchical Risk Parity (HRP)
- Black-Litterman Model

قواعدك:
📊 Max 40% في أي أصل واحد
📊 Min 10% كاش دائماً
📊 Rebalancing كل شهر أو عند تغيير الـ regime
📊 Correlation < 0.7 بين الأصول المختارة

مخرجاتك:
```
💼 PORTFOLIO RECOMMENDATION
━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 التوزيع المقترح:
  BTC:        [X]%  ($[Y])
  ETH:        [X]%  ($[Y])
  [أصل 3]:   [X]%  ($[Y])
  USDT/Cash:  [X]%  ($[Y])

📈 Rebalancing المطلوب:
  • [بيع X من Y]
  • [شراء X من Z]

🎯 الهدف: Sharpe Ratio > [X]
⚠️  التحذيرات: [أي مخاطر]
```"""

    def get_regime_allocation(self, regime: str, total: float) -> dict:
        alloc = self.REGIME_ALLOCATION.get(regime, self.REGIME_ALLOCATION["sideways"])
        return {k: {"pct": v, "usd": round(total * v / 100, 2)} for k, v in alloc.items()}

    async def analyze_portfolio(self, portfolio: PortfolioState, regime: str,
                                 user_id: str = "system") -> AgentResponse:
        current = "\n".join([
            f"  {a.symbol}: {a.allocation_pct:.1f}% (${a.current_value:.0f}) | P&L: {a.pnl_pct:+.1f}%"
            for a in portfolio.assets
        ])
        suggested = self.get_regime_allocation(regime, portfolio.total_value)

        context = AgentContext(
            user_id=user_id,
            user_message=f"""حلّل المحفظة الحالية واقترح تحسينات:

القيمة الإجمالية: ${portfolio.total_value:,.0f} USDT
الـ Regime الحالي: {regime}

التوزيع الحالي:
{current}
  Cash: {portfolio.cash_pct}%

التوزيع المقترح للـ regime ({regime}):
{chr(10).join([f"  {k}: {v['pct']}% (${v['usd']:.0f})" for k, v in suggested.items()])}

اقترح:
1. هل التوزيع الحالي مناسب؟
2. ما الـ rebalancing المطلوب؟
3. أي أصول تضيف أو تحذف؟"""
        )
        return await self.think(context)
