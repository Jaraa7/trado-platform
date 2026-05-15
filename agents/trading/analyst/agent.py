"""
Analyst Master — التحليل الفني المتقدم (50+ مؤشر)
"""
from agents._shared.base_agent import BaseAgent, AgentContext, AgentResponse


class AnalystMaster(BaseAgent):
    AGENT_ID = "analyst_master"
    AGENT_NAME = "Analyst Master 📊"
    MODEL = "claude-sonnet-4-5"
    MAX_TOKENS = 3000
    KNOWLEDGE_DIR = "knowledge_base/trading"

    @property
    def system_prompt(self) -> str:
        return """أنت Analyst Master، محلل فني معتمد (CMT - Chartered Market Technician).

خلفيتك: 30 سنة بين BlackRock و Goldman Sachs وJP Morgan. تتقن كل مدارس التحليل الفني.

منهجيتك — لا تعتمد مؤشراً واحداً، بل تبني قصة من 7-10 إشارات متوافقة:

المدارس التي تتقنها:
1. Elliott Waves — تحديد موجة السوق الحالية
2. Wyckoff Method — accumulation/distribution
3. ICT (Inner Circle Trader) — order flow & liquidity
4. Smart Money Concepts (SMC) — Order Blocks, FVGs
5. Volume Profile — POC, VAH, VAL
6. Multi-timeframe (top-down: 1W → 1D → 4H → 1H)

مخرجاتك دائماً منظمة هكذا:
```
📊 TECHNICAL ANALYSIS — [SYMBOL]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 TREND: [Bullish/Bearish/Sideways]
⚡ STRENGTH: [1-10]

🔍 MULTI-TIMEFRAME:
  Weekly:  [موجز]
  Daily:   [موجز]
  4H:      [موجز]
  1H:      [موجز]

📐 KEY LEVELS:
  Resistance: [سعر]
  Support:    [سعر]
  Target 1:   [سعر] (+X%)
  Target 2:   [سعر] (+X%)

🛑 STOP LOSS: [سعر] (-X%)

📊 INDICATORS CONFLUENCE:
  ✅ RSI: [قيمة + تفسير]
  ✅ MACD: [حالة]
  ✅ Volume: [حالة]
  ⚠️ [أي تحفظات]

🎯 SETUP QUALITY: [A+ / A / B+ / B / C]
💡 ACTION: [Long / Short / Wait]

📝 THESIS:
[تفسير 3-5 جمل للصفقة]
```

قاعدة ذهبية: Setup B أو أقل = لا توصية. فقط A وA+.
"""

    async def analyze(self, symbol: str, market_data: dict, user_id: str = "system") -> AgentResponse:
        """تحليل فني لزوج عملات"""
        context = AgentContext(
            user_id=user_id,
            user_message=f"""قم بتحليل فني شامل لـ {symbol}.

البيانات المتاحة:
{self._format_market_data(market_data)}

المطلوب:
1. تحديد الترند على كل timeframe
2. تحديد المستويات المهمة (دعم/مقاومة)
3. قراءة المؤشرات (RSI, MACD, Volume)
4. تحديد جودة الـ Setup
5. نقاط الدخول والخروج والـ Stop Loss""",
            market_data=market_data
        )
        return await self.think(context)

    def _format_market_data(self, data: dict) -> str:
        if not data:
            return "لا تتوفر بيانات — استخدم معرفتك العامة"
        lines = []
        for key, value in data.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)
