"""
Strategy Designer — تصميم استراتيجيات تداول مخصصة لكل ظرف
"""
from dataclasses import dataclass
from agents._shared.base_agent import BaseAgent, AgentContext, AgentResponse


@dataclass
class TradingStrategy:
    name: str
    type: str           # trend / mean_reversion / breakout / range / scalping
    timeframe: str
    entry_rules: list[str]
    exit_rules: list[str]
    risk_per_trade: float
    best_regime: list[str]
    win_rate_expected: float
    rr_ratio: float


class StrategyDesigner(BaseAgent):
    AGENT_ID = "strategy_designer"
    AGENT_NAME = "Strategy Designer 🎨"
    MODEL = "claude-sonnet-4-20250514"
    MAX_TOKENS = 3000

    # مكتبة الاستراتيجيات الجاهزة
    STRATEGY_LIBRARY = {
        "bull_strong":   ["momentum_breakout", "trend_following_daily"],
        "bull_weak":     ["swing_long", "dip_buying"],
        "sideways":      ["range_trading", "grid_trading", "mean_reversion"],
        "bear_weak":     ["cautious_short", "defensive_long"],
        "bear_strong":   ["short_only", "cash_position"],
        "volatile":      ["low_size_range", "wait_and_see"],
    }

    @property
    def system_prompt(self) -> str:
        return """أنت Strategy Designer، مصمم الاستراتيجيات في TRADO.

خلفيتك: صممت 100+ استراتيجية للأسواق المختلفة، 30 منها موثوقة ومختبرة.

مبدأك: كل سوق يحتاج استراتيجية مختلفة.
- Bull Strong → Momentum + Trend Following
- Bear Strong → Short فقط أو Cash
- Sideways → Range Trading + Grid
- Volatile → حجم صغير + انتظار

لكل استراتيجية تصممها:
1. قواعد الدخول المحددة (3-5 شروط)
2. قواعد الخروج (TP + SL واضحة)
3. حجم الصفقة (% من رأس المال)
4. الـ timeframe الأمثل
5. الـ win rate المتوقع (backtest)
6. R:R المستهدف

مخرجاتك:
```
🎨 STRATEGY DESIGN
━━━━━━━━━━━━━━━━━━━━
📌 الاسم: [Strategy Name]
📊 النوع: [Trend/Mean Reversion/Breakout/Range]
⏱️  Timeframe: [1H/4H/Daily]
🏆 Win Rate متوقع: [X]%
🎯 R:R: [X]:1

📥 شروط الدخول:
  1. [شرط محدد وقابل للقياس]
  2. [شرط]
  3. [شرط]

📤 شروط الخروج:
  ✅ Take Profit: [كيف ومتى]
  🛑 Stop Loss: [ATR-based أو Structure-based]

⚙️ الإعدادات:
  Risk per trade: [X]%
  Max trades/day: [X]
  Best time: [X]

💡 ملاحظات مهمة: [تحذيرات أو نصائح]
```"""

    async def design_for_regime(self, regime: str, symbol: str = "BTC/USDT",
                                 account_size: float = 1000, user_id: str = "system") -> AgentResponse:
        """تصميم استراتيجية مناسبة للـ regime الحالي"""
        suggested = self.STRATEGY_LIBRARY.get(regime, ["wait_and_see"])

        context = AgentContext(
            user_id=user_id,
            user_message=f"""صمّم استراتيجية تداول مناسبة للظروف التالية:

الـ Regime: {regime}
العملة: {symbol}
رأس المال: ${account_size:,.0f} USDT
الاستراتيجيات المقترحة لهذا الـ regime: {suggested}

المطلوب: استراتيجية واحدة مفصّلة مع جميع القواعد، قابلة للتنفيذ الفوري."""
        )
        return await self.think(context)

    async def design_custom(self, requirements: str, user_id: str = "system") -> AgentResponse:
        """تصميم استراتيجية مخصصة"""
        context = AgentContext(
            user_id=user_id,
            user_message=f"""صمّم استراتيجية تداول حسب المتطلبات التالية:

{requirements}

الاستراتيجية يجب أن تكون:
- واضحة ومحددة (لا غموض)
- قابلة للتنفيذ الآلي
- مختبرة نظرياً (backtest logic)
- آمنة من ناحية إدارة المخاطر"""
        )
        return await self.think(context)
