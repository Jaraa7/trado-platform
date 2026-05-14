"""
Sentiment Analyzer — قياس مشاعر السوق من Social Media
"""
from dataclasses import dataclass
from agents._shared.base_agent import BaseAgent, AgentContext, AgentResponse


@dataclass
class SentimentScore:
    overall: float       # -1 (bearish) to +1 (bullish)
    fear_greed: int      # 0-100
    label: str           # Extreme Fear / Fear / Neutral / Greed / Extreme Greed
    bullish_pct: float
    bearish_pct: float
    neutral_pct: float
    contrarian_signal: str  # buy / sell / hold


class SentimentAnalyzer(BaseAgent):
    AGENT_ID = "sentiment_analyzer"
    AGENT_NAME = "Sentiment Analyzer 💭"
    MODEL = "claude-haiku-4-5-20251001"
    MAX_TOKENS = 1200

    @property
    def system_prompt(self) -> str:
        return """أنت Sentiment Analyzer، قارئ مشاعر السوق.

خلفيتك: تقرأ آلاف التغريدات والمنشورات يومياً. تكشف الـ Fear والـ Greed قبل أن ينعكس في السعر.

فلسفتك — Contrarian Thinking:
📈 عندما الجميع "BULLISH جداً" = وقت البيع
📉 عندما الجميع "BEARISH ويائسون" = وقت الشراء

مؤشرات تراقبها:
- Fear & Greed Index (0-100)
- Twitter/X sentiment للـ BTC وETH
- Reddit r/CryptoCurrency mood
- Telegram channels sentiment
- FOMO waves / FUD waves

مخرجاتك:
```
💭 SENTIMENT REPORT
━━━━━━━━━━━━━━━━━━━━
😨 Fear & Greed: [X]/100 — [Extreme Fear/Fear/Neutral/Greed/Extreme Greed]
📊 Bullish: [X]% | Bearish: [X]% | Neutral: [X]%

🔍 Social Media:
  Twitter: [mood]
  Reddit:  [mood]
  Telegram: [mood]

⚡ Contrarian Signal: [BUY/SELL/HOLD]
💡 السبب: [جملتان]
```

قاعدة: Fear < 20 = فرصة شراء | Greed > 80 = خطر"""

    async def get_fear_greed(self) -> dict:
        """جلب مؤشر Fear & Greed"""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get("https://api.alternative.me/fng/?limit=1")
                if r.status_code == 200:
                    data = r.json()["data"][0]
                    value = int(data["value"])
                    label = data["value_classification"]
                    return {"value": value, "label": label}
        except Exception:
            pass
        return {"value": 50, "label": "Neutral"}

    def interpret_score(self, score: int) -> SentimentScore:
        """تفسير مؤشر الخوف والجشع"""
        if score <= 20:
            label = "Extreme Fear"
            overall = -0.8
            contrarian = "buy"
        elif score <= 40:
            label = "Fear"
            overall = -0.4
            contrarian = "buy"
        elif score <= 60:
            label = "Neutral"
            overall = 0.0
            contrarian = "hold"
        elif score <= 80:
            label = "Greed"
            overall = 0.4
            contrarian = "sell"
        else:
            label = "Extreme Greed"
            overall = 0.8
            contrarian = "sell"

        bullish = (score / 100) * 70 + 15
        bearish = ((100 - score) / 100) * 70 + 15
        neutral = 100 - bullish - bearish + 30

        return SentimentScore(
            overall=overall,
            fear_greed=score,
            label=label,
            bullish_pct=round(bullish, 1),
            bearish_pct=round(bearish, 1),
            neutral_pct=max(0, round(100 - bullish - bearish, 1)),
            contrarian_signal=contrarian
        )

    async def analyze(self, coin: str = "BTC", user_id: str = "system") -> AgentResponse:
        fg_data = await self.get_fear_greed()
        score = self.interpret_score(fg_data["value"])

        context = AgentContext(
            user_id=user_id,
            user_message=f"""حلّل مشاعر السوق الحالية لـ {coin}:

Fear & Greed Index: {fg_data['value']}/100 ({fg_data['label']})
التفسير الأولي: {score.contrarian_signal.upper()} signal
Bullish: {score.bullish_pct}% | Bearish: {score.bearish_pct}%

بناءً على هذه البيانات + معرفتك بالسوق العام:
1. هل الـ sentiment يدعم صفقة long أم short على {coin}؟
2. ما مستوى FOMO أو FUD الحالي؟
3. التوصية النهائية (contrarian thinking)"""
        )
        return await self.think(context)
