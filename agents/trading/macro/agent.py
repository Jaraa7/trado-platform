"""
Macro Economist — تحليل الاقتصاد الكلي وتأثيره على الكريبتو
"""
from dataclasses import dataclass
from agents._shared.base_agent import BaseAgent, AgentContext, AgentResponse


@dataclass
class MacroEvent:
    name: str
    date: str
    actual: str = ""
    forecast: str = ""
    previous: str = ""
    impact: str = "medium"   # high / medium / low
    crypto_effect: str = ""  # bullish / bearish / neutral


class MacroEconomist(BaseAgent):
    AGENT_ID = "macro_economist"
    AGENT_NAME = "Macro Economist 🏛️"
    MODEL = "claude-sonnet-4-5"
    MAX_TOKENS = 2000

    @property
    def system_prompt(self) -> str:
        return """أنت Macro Economist، دكتوراه اقتصاد من جامعة شيكاغو.

خلفيتك: 30 سنة تحليل اقتصاد كلي للأسواق المالية الكبرى.

فهمك: الكريبتو لا يعيش في فقاعة — Fed rates, CPI, DXY, S&P 500, Gold — كلها تؤثر.

العلاقات الرئيسية:
📉 Fed يرفع الفائدة → DXY↑ → BTC↓ (عموماً)
📈 Fed يخفض الفائدة → السيولة↑ → BTC↑
📊 CPI أعلى من التوقعات → تشدد Fed → BTC↓
💵 M2 يتوسع → أصول خطرة ترتفع → BTC↑
📈 S&P 500 correlation مع BTC: ~0.65 في الأوقات العادية

تحليلك يشمل:
- قرارات Fed (هل سيرفع/يثبت/يخفض؟)
- CPI ومسار التضخم
- DXY اتجاه الدولار
- سيولة السوق العالمية (M2)
- appetite للمخاطرة (risk-on/risk-off)

مخرجاتك:
```
🏛️ MACRO ANALYSIS
━━━━━━━━━━━━━━━━━━━━
🌍 البيئة الماكرو: [Risk-On / Risk-Off / Neutral]
💵 Fed Stance: [Hawkish / Neutral / Dovish]
📊 DXY Trend: [↑ Strengthening / → Stable / ↓ Weakening]
💧 Global Liquidity: [Expanding / Contracting / Stable]

🪙 تأثير على BTC/كريبتو:
  قصير المدى (أسابيع): [↑/→/↓ + سبب]
  متوسط المدى (أشهر): [↑/→/↓ + سبب]

⚡ الأحداث القادمة المهمة:
  • [حدث + تاريخه + تأثيره المتوقع]

🎯 الموقف الاستراتيجي: [جملة واحدة]
```"""

    async def analyze_macro(self, user_id: str = "system") -> AgentResponse:
        """تحليل ماكرو شامل"""
        context = AgentContext(
            user_id=user_id,
            user_message="""قدّم تحليلاً ماكرو اقتصادياً شاملاً للوضع الراهن وتأثيره على سوق الكريبتو.

بناءً على معرفتك الراهنة، حلّل:
1. موقف الـ Fed الحالي ومسار أسعار الفائدة
2. اتجاه مؤشر الدولار (DXY)
3. بيئة السيولة العالمية
4. علاقة S&P500 مع BTC حالياً
5. هل نحن في بيئة Risk-On أم Risk-Off؟
6. أهم 3 أحداث ماكرو قادمة وتأثيرها"""
        )
        return await self.think(context)

    async def analyze_event(self, event: MacroEvent, user_id: str = "system") -> AgentResponse:
        """تحليل حدث ماكرو محدد"""
        context = AgentContext(
            user_id=user_id,
            user_message=f"""حلّل هذا الحدث الاقتصادي وتأثيره على الكريبتو:

الحدث: {event.name}
التاريخ: {event.date}
القيمة الفعلية: {event.actual or 'لم تصدر بعد'}
التوقعات: {event.forecast}
السابق: {event.previous}

ما التأثير المتوقع على BTC وسوق الكريبتو؟
هل يجب التحرك قبل أم بعد الإعلان؟"""
        )
        return await self.think(context)
