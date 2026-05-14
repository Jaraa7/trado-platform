"""
News Analyst — تحليل الأخبار وتأثيرها على السوق فوراً
"""
import httpx
import asyncio
from dataclasses import dataclass
from agents._shared.base_agent import BaseAgent, AgentContext, AgentResponse


@dataclass
class NewsItem:
    title: str
    source: str
    url: str = ""
    published_at: str = ""
    sentiment: str = "neutral"   # bullish / bearish / neutral
    impact: int = 0              # 1-10
    related_coins: list = None

    def __post_init__(self):
        if self.related_coins is None:
            self.related_coins = []


class NewsAnalyst(BaseAgent):
    AGENT_ID = "news_analyst"
    AGENT_NAME = "News Analyst 📰"
    MODEL = "claude-sonnet-4-20250514"
    MAX_TOKENS = 2000

    @property
    def system_prompt(self) -> str:
        return """أنت News Analyst، خبير تحليل الأخبار المالية في سوق الكريبتو.

خلفيتك: 30 سنة في غرف الأخبار المالية لـ Bloomberg وReuters.
تعرف الفرق بين خبر "بيتكوين يرتفع" وخبر "BlackRock يقدم طلب ETF".

معايير التصنيف:
- المصدر: هل هو موثوق؟ (Bloomberg=10، تغريدة مجهولة=2)
- التأثير: كم يؤثر على السعر؟ (1-10)
- السرعة: هل يحتاج رد فعل فوري؟
- الوزن: هل هو خبر حقيقي أم pump & dump؟

مخرجاتك:
```
📰 NEWS ANALYSIS
━━━━━━━━━━━━━━━━━━━━
📌 الخبر: [عنوان مختصر]
📡 المصدر: [المصدر + مصداقية X/10]
⚡ التأثير: [X/10]
📊 الاتجاه: [🟢 Bullish / 🔴 Bearish / ⚪ Neutral]
🪙 العملات المتأثرة: [قائمة]
⏱️  الإجراء: [فوري/خلال ساعة/يراقب/يتجاهل]

💡 التحليل: [3 جمل]
🎯 التوصية: [ماذا يفعل المتداول]
```

قاعدة ذهبية: خبر تأثير < 5 = لا توصية. فقط 6+."""

    async def fetch_crypto_news(self) -> list[NewsItem]:
        """جلب الأخبار من APIs المتاحة"""
        news = []

        # CryptoPanic API (free tier)
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    "https://cryptopanic.com/api/v1/posts/",
                    params={"auth_token": "free", "filter": "hot", "kind": "news"}
                )
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("results", [])[:10]:
                        news.append(NewsItem(
                            title=item.get("title", ""),
                            source=item.get("source", {}).get("title", "Unknown"),
                            url=item.get("url", ""),
                            published_at=item.get("published_at", ""),
                            related_coins=[
                                c.get("code", "") for c in item.get("currencies", [])
                            ]
                        ))
        except Exception:
            # Fallback: أخبار وهمية للتطوير
            news = [
                NewsItem("Bitcoin ETF sees record inflows", "Bloomberg", impact=8, sentiment="bullish"),
                NewsItem("Fed signals rate cut in Q3", "Reuters", impact=7, sentiment="bullish"),
                NewsItem("Major exchange hack reported", "CoinDesk", impact=9, sentiment="bearish"),
            ]

        return news

    async def analyze_news(self, user_id: str = "system") -> AgentResponse:
        """تحليل أحدث الأخبار"""
        news_items = await self.fetch_crypto_news()

        news_text = "\n".join([
            f"- [{item.source}] {item.title}"
            for item in news_items[:8]
        ])

        context = AgentContext(
            user_id=user_id,
            user_message=f"""حلّل هذه الأخبار وحدد تأثيرها على سوق الكريبتو:

{news_text}

المطلوب:
1. صنّف كل خبر (تأثير 1-10 + bullish/bearish)
2. حدد الأخبار الحرجة (تأثير 7+)
3. العملات المتأثرة لكل خبر
4. التوصية الفورية للمتداولين"""
        )
        return await self.think(context)

    async def analyze_single(self, headline: str, source: str = "Unknown", user_id: str = "system") -> AgentResponse:
        """تحليل خبر واحد"""
        context = AgentContext(
            user_id=user_id,
            user_message=f"حلّل هذا الخبر من {source}:\n\n\"{headline}\"\n\nما تأثيره على السوق؟ هل يستوجب رد فعل فوري؟"
        )
        return await self.think(context)
