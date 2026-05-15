"""
Risk Guardian — حارس رأس المال. الـ "فرامل" في النظام.
"""
from dataclasses import dataclass
from agents._shared.base_agent import BaseAgent, AgentContext, AgentResponse
from config.settings import settings


@dataclass
class TradeProposal:
    symbol: str
    direction: str        # "long" | "short"
    entry_price: float
    stop_loss: float
    take_profit: float
    account_balance: float
    leverage: int = 1
    proposed_size: float = 0.0


@dataclass
class RiskDecision:
    approved: bool
    reason: str
    recommended_size: float = 0.0
    risk_percentage: float = 0.0
    risk_reward: float = 0.0
    veto_applied: bool = False


class RiskGuardian(BaseAgent):
    AGENT_ID = "risk_guardian"
    AGENT_NAME = "Risk Guardian 🛡️"
    MODEL = "claude-sonnet-4-5"
    MAX_TOKENS = 1500

    # القواعد الصارمة
    MAX_RISK_PER_TRADE = settings.max_risk_per_trade    # 2% من رأس المال (خسارة محتملة)
    MAX_DAILY_LOSS = settings.max_daily_loss             # 6%
    MAX_DRAWDOWN = settings.max_monthly_drawdown         # 15%
    MAX_LEVERAGE = settings.max_leverage                 # 3x
    MIN_RISK_REWARD = 1.5                               # R:R >= 1.5
    MAX_POSITION_CONCENTRATION = 0.30                   # 🆕 max 30% رأس المال في صفقة واحدة

    @property
    def system_prompt(self) -> str:
        return f"""أنت Risk Guardian، حارس رأس المال في TRADO.

خلفيتك: 30 سنة في إدارة مخاطر — شهدت انهيار LTCM 1998، Lehman 2008، Archegos 2021.
شعارك: "الدفاع عن رأس المال أهم من الربح."

القواعد الصارمة (لا استثناءات أبداً):
🚫 Max {self.MAX_RISK_PER_TRADE*100:.0f}% خطر لكل صفقة
🚫 Max {self.MAX_DAILY_LOSS*100:.0f}% خسارة يومية (بعدها يتوقف التداول)
🚫 Max {self.MAX_DRAWDOWN*100:.0f}% drawdown شهري
🚫 Max {self.MAX_LEVERAGE}x leverage
🚫 Min R:R = {self.MIN_RISK_REWARD}:1

عند تقييم صفقة، تقدم:
```
🛡️ RISK ASSESSMENT — [SYMBOL]
━━━━━━━━━━━━━━━━━━━━━━━━━━

✅/❌ القرار: [APPROVED / REJECTED]
⚠️  السبب: [تفسير واضح]

📊 الحسابات:
  • حجم الصفقة المقترح: [X] USDT
  • المخاطرة: [X]% من رأس المال
  • R:R: [X]:1
  • SL المسافة: [X]%

💡 التوصية: [حجم مناسب إذا تم الرفض]
```

تملك حق الـ VETO المطلق على أي صفقة."""

    def calculate_position_size(self, proposal: TradeProposal) -> RiskDecision:
        """حساب حجم الصفقة الصحيح"""
        if proposal.entry_price <= 0 or proposal.stop_loss <= 0:
            return RiskDecision(
                approved=False,
                reason="بيانات الصفقة غير صحيحة",
                veto_applied=True
            )

        # حساب المسافة للـ SL
        if proposal.direction == "long":
            sl_distance = abs(proposal.entry_price - proposal.stop_loss) / proposal.entry_price
            tp_distance = abs(proposal.take_profit - proposal.entry_price) / proposal.entry_price
        else:
            sl_distance = abs(proposal.stop_loss - proposal.entry_price) / proposal.entry_price
            tp_distance = abs(proposal.entry_price - proposal.take_profit) / proposal.entry_price

        if sl_distance <= 0:
            return RiskDecision(approved=False, reason="Stop Loss غير صحيح", veto_applied=True)

        # حساب R:R
        risk_reward = tp_distance / sl_distance if sl_distance > 0 else 0

        # تحقق من R:R
        if risk_reward < self.MIN_RISK_REWARD:
            return RiskDecision(
                approved=False,
                reason=f"R:R = {risk_reward:.2f} أقل من الحد الأدنى {self.MIN_RISK_REWARD}",
                risk_reward=risk_reward,
                veto_applied=True
            )

        # حساب الحجم الصحيح (من ناحية الخسارة)
        max_risk_amount = proposal.account_balance * self.MAX_RISK_PER_TRADE
        position_size = max_risk_amount / sl_distance

        # 🆕 فحص Concentration Risk
        max_position_size = proposal.account_balance * self.MAX_POSITION_CONCENTRATION
        if position_size > max_position_size:
            # نطبّق الحد الأكثر صرامة
            position_size = max_position_size
            concentration_pct = position_size / proposal.account_balance * 100
            actual_risk_pct = (position_size * sl_distance) / proposal.account_balance * 100
        else:
            concentration_pct = position_size / proposal.account_balance * 100
            actual_risk_pct = self.MAX_RISK_PER_TRADE * 100

        # تحقق من الـ leverage
        if proposal.leverage > self.MAX_LEVERAGE:
            return RiskDecision(
                approved=False,
                reason=f"Leverage {proposal.leverage}x يتجاوز الحد {self.MAX_LEVERAGE}x",
                veto_applied=True
            )

        return RiskDecision(
            approved=True,
            reason=f"Size: {concentration_pct:.1f}% من رأس المال | Risk: {actual_risk_pct:.2f}% | R:R {risk_reward:.2f}",
            recommended_size=round(position_size, 2),
            risk_percentage=round(actual_risk_pct, 2),
            risk_reward=round(risk_reward, 2)
        )

    async def evaluate_trade(self, proposal: TradeProposal, user_id: str = "system") -> AgentResponse:
        """تقييم صفقة مقترحة"""
        decision = self.calculate_position_size(proposal)

        context = AgentContext(
            user_id=user_id,
            user_message=f"""تقييم صفقة مقترحة:
Symbol: {proposal.symbol}
Direction: {proposal.direction}
Entry: {proposal.entry_price}
Stop Loss: {proposal.stop_loss}
Take Profit: {proposal.take_profit}
Balance: {proposal.account_balance} USDT
Leverage: {proposal.leverage}x

الحسابات الأولية:
- القرار: {'✅ موافق' if decision.approved else '❌ مرفوض'}
- السبب: {decision.reason}
- الحجم المقترح: {decision.recommended_size} USDT
- R:R: {decision.risk_reward}

قدم تقريرك الكامل."""
        )
        return await self.think(context)
