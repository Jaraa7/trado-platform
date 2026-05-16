"""
📰 TradoAI — News Sources (Production Ready)
مصادر الأخبار المُختبرة والعاملة

✅ RSS Feeds (Server-side — no CORS):
   - Cointelegraph ✅ مُختبر
   - CoinDesk ✅ (server)
   - Decrypt ✅ (server)
   - Bitcoin Magazine ✅ (server)

ملاحظة: RSS لا تعمل من المتصفح بسبب CORS لكن تعمل من Fly.io
"""
import asyncio
import httpx
import xml.etree.ElementTree as ET
import re
from datetime import datetime
from loguru import logger
from cache import Cache

RSS_FEEDS = {
    "cointelegraph":  "https://cointelegraph.com/rss",
    "coindesk":       "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "decrypt":        "https://decrypt.co/feed",
    "bitcoinmagazine":"https://bitcoinmagazine.com/feed",
    "theblock":       "https://www.theblock.co/rss.xml",
}

async def _fetch_rss(url: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True,
            headers={"User-Agent": "TradoAI/1.0 (crypto news aggregator)"}) as c:
            r = await c.get(url)
            r.raise_for_status()
            return r.text
    except Exception as e:
        logger.warning(f"RSS fetch {url[:50]}: {e}")
        return ""

def _strip_html(text: str) -> str:
    return re.sub(r'<[^>]+>', '', text or '').strip()[:300]

def _simple_sentiment(title: str) -> str:
    title_lower = title.lower()
    bullish_words = ["surge", "soar", "rally", "bullish", "gain", "high", "rise",
                     "adoption", "partnership", "launch", "upgrade", "breakout",
                     "ارتفع", "صعد", "نمو", "إطلاق"]
    bearish_words = ["crash", "drop", "fall", "bearish", "decline", "low", "ban",
                     "hack", "scam", "liquidation", "fear", "concern", "risk",
                     "هبط", "انخفض", "خسر", "حظر"]
    bull = sum(1 for w in bullish_words if w in title_lower)
    bear = sum(1 for w in bearish_words if w in title_lower)
    if bull > bear:   return "bullish"
    if bear > bull:   return "bearish"
    return "neutral"


class RSSSource:

    @staticmethod
    async def get_feed(source: str = "cointelegraph", limit: int = 10) -> list:
        cache_key = Cache.make_key("rss", source)
        if c := await Cache.get(cache_key):
            return c

        url      = RSS_FEEDS.get(source, RSS_FEEDS["cointelegraph"])
        xml_text = await _fetch_rss(url)
        if not xml_text:
            return []

        try:
            root  = ET.fromstring(xml_text)
            chan  = root.find("channel")
            items = (chan or root).findall("item")

            news = []
            for item in items[:limit]:
                title = _strip_html(item.findtext("title", ""))
                link  = item.findtext("link", "").strip()
                pub   = item.findtext("pubDate", "").strip()
                desc  = _strip_html(item.findtext("description", ""))
                if not title:
                    continue
                news.append({
                    "title":     title,
                    "url":       link,
                    "source":    source,
                    "published": pub,
                    "summary":   desc,
                    "sentiment": _simple_sentiment(title),
                })

            await Cache.set(cache_key, news, ttl=600)
            return news

        except Exception as e:
            logger.error(f"RSS parse ({source}): {e}")
            return []

    @staticmethod
    async def get_all(limit_per: int = 5) -> list:
        """كل الـ feeds بالتوازي"""
        results = await asyncio.gather(
            *[RSSSource.get_feed(src, limit_per) for src in RSS_FEEDS],
            return_exceptions=True
        )
        all_news = []
        for r in results:
            if isinstance(r, list):
                all_news.extend(r)
        return all_news


class NewsAggregator:

    @staticmethod
    async def get_summary() -> dict:
        cache_key = Cache.make_key("news_summary", "market")
        if c := await Cache.get(cache_key):
            return c

        all_news = await RSSSource.get_all(limit_per=8)

        bullish = sum(1 for n in all_news if n.get("sentiment") == "bullish")
        bearish = sum(1 for n in all_news if n.get("sentiment") == "bearish")
        total   = bullish + bearish

        sentiment = "neutral"
        if total > 0:
            ratio = bullish / total
            sentiment = "bullish" if ratio > 0.6 else "bearish" if ratio < 0.4 else "neutral"

        result = {
            "total_articles":   len(all_news),
            "market_sentiment": sentiment,
            "bullish_pct":      round(bullish / total * 100, 1) if total > 0 else 50,
            "top_news":         all_news[:10],
            "ts":               datetime.utcnow().isoformat(),
        }
        await Cache.set(cache_key, result, ttl=600)
        return result

    @staticmethod
    async def get_coin_news(symbol: str, limit: int = 5) -> list:
        """أخبار تخص عملة معينة"""
        coin = symbol.split("/")[0].lower()
        all_news = await RSSSource.get_all(limit_per=10)
        relevant = [n for n in all_news
                    if coin in n["title"].lower() or coin in n.get("summary","").lower()]
        return relevant[:limit]
