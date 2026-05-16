"""
📰 TradoAI — News & Sentiment Sources
مصادر الأخبار والمعنويات

المصادر:
- CryptoPanic API (أخبار + معنويات)
- RSS Feeds (CoinDesk, The Block, Decrypt, Cointelegraph)
- Santiment (Social sentiment)
- Twitter/X API (trending crypto topics)
- Reddit API (r/CryptoCurrency sentiment)
"""
import os
import asyncio
import httpx
import xml.etree.ElementTree as ET
from datetime import datetime
from loguru import logger
from cache import Cache


CRYPTOPANIC_KEY = os.getenv("CRYPTOPANIC_API_KEY", "")
SANTIMENT_KEY   = os.getenv("SANTIMENT_API_KEY", "")


async def _get(url: str, **kwargs) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(url, **kwargs)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.warning(f"News fetch error: {url[:60]} → {e}")
        return {}

async def _get_text(url: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(url)
            return r.text
    except Exception as e:
        logger.warning(f"RSS fetch error: {url[:60]} → {e}")
        return ""


# ════════════════════════════════════════════════════════════════════
# 1. CRYPTOPANIC
# ════════════════════════════════════════════════════════════════════

class CryptoPanicSource:
    BASE = "https://cryptopanic.com/api/v1/posts"

    @staticmethod
    async def get_news(currencies: list = None, filter: str = "hot",
                       limit: int = 20) -> list:
        """
        جلب الأخبار من CryptoPanic
        filter: 'hot' | 'rising' | 'bullish' | 'bearish' | 'important'
        """
        cache_key = Cache.make_key("news_cryptopanic", filter, str(currencies or []))
        cached = await Cache.get(cache_key)
        if cached:
            return cached

        params = {
            "auth_token": CRYPTOPANIC_KEY or "public",
            "filter":      filter,
            "public":      "true",
        }
        if currencies:
            params["currencies"] = ",".join(currencies)

        data = await _get(CryptoPanicSource.BASE, params=params)
        results = data.get("results", [])

        news = [{
            "id":         r.get("id"),
            "title":      r.get("title", ""),
            "url":        r.get("url", ""),
            "source":     r.get("source", {}).get("title", ""),
            "published":  r.get("published_at", ""),
            "currencies": [c.get("code") for c in r.get("currencies", [])],
            "votes": {
                "positive": r.get("votes", {}).get("positive", 0),
                "negative": r.get("votes", {}).get("negative", 0),
                "important": r.get("votes", {}).get("important", 0),
            },
            "sentiment": CryptoPanicSource._calc_sentiment(r.get("votes", {})),
        } for r in results[:limit]]

        await Cache.set(cache_key, news, ttl=300)
        return news

    @staticmethod
    def _calc_sentiment(votes: dict) -> str:
        pos = votes.get("positive", 0)
        neg = votes.get("negative", 0)
        if pos == 0 and neg == 0:
            return "neutral"
        ratio = pos / (pos + neg)
        if ratio >= 0.65:
            return "bullish"
        if ratio <= 0.35:
            return "bearish"
        return "neutral"

    @staticmethod
    async def get_coin_news(symbol: str) -> list:
        """أخبار عملة محددة"""
        coin = symbol.split("/")[0]
        return await CryptoPanicSource.get_news(currencies=[coin])


# ════════════════════════════════════════════════════════════════════
# 2. RSS FEEDS
# ════════════════════════════════════════════════════════════════════

RSS_FEEDS = {
    "coindesk":      "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "cointelegraph": "https://cointelegraph.com/rss",
    "decrypt":       "https://decrypt.co/feed",
    "theblock":      "https://www.theblock.co/rss.xml",
    "bitcoinmagazine":"https://bitcoinmagazine.com/feed",
}

class RSSSource:

    @staticmethod
    async def get_feed(source: str = "coindesk", limit: int = 10) -> list:
        """جلب RSS feed وتحويله لقائمة أخبار"""
        cache_key = Cache.make_key("rss", source)
        cached = await Cache.get(cache_key)
        if cached:
            return cached

        url = RSS_FEEDS.get(source, RSS_FEEDS["coindesk"])
        xml_text = await _get_text(url)
        if not xml_text:
            return []

        try:
            root = ET.fromstring(xml_text)
            channel = root.find("channel")
            items = channel.findall("item") if channel else root.findall(".//item")

            news = []
            for item in items[:limit]:
                title = item.findtext("title", "").strip()
                link  = item.findtext("link", "").strip()
                pub   = item.findtext("pubDate", "").strip()
                desc  = item.findtext("description", "").strip()
                # Remove HTML tags
                import re
                desc = re.sub(r'<[^>]+>', '', desc)[:300]

                news.append({
                    "title":     title,
                    "url":       link,
                    "source":    source,
                    "published": pub,
                    "summary":   desc,
                    "sentiment": "neutral",
                })

            await Cache.set(cache_key, news, ttl=600)
            return news

        except Exception as e:
            logger.error(f"RSS parse error ({source}): {e}")
            return []

    @staticmethod
    async def get_all_feeds(limit_per_source: int = 5) -> list:
        """كل الـ feeds في وقت واحد"""
        tasks = [RSSSource.get_feed(src, limit_per_source) for src in RSS_FEEDS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_news = []
        for r in results:
            if isinstance(r, list):
                all_news.extend(r)
        # ترتيب حسب التاريخ (الأحدث أولاً)
        return sorted(all_news, key=lambda x: x.get("published", ""), reverse=True)


# ════════════════════════════════════════════════════════════════════
# 3. SANTIMENT (Social Sentiment)
# ════════════════════════════════════════════════════════════════════

class SantimentSource:

    @staticmethod
    async def get_social_volume(coin: str = "bitcoin") -> dict:
        """حجم الاهتمام الاجتماعي بالعملة"""
        if not SANTIMENT_KEY:
            return {"coin": coin, "social_volume": 0, "source": "unavailable"}

        cache_key = Cache.make_key("social_vol", coin)
        cached = await Cache.get(cache_key)
        if cached:
            return cached

        query = """
        {
          getMetric(metric: "social_volume_total") {
            timeseriesData(
              slug: "%s"
              from: "utc_now-1d"
              to: "utc_now"
              interval: "1h"
            ) { datetime value }
          }
        }
        """ % coin

        try:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.post(
                    "https://api.santiment.net/graphql",
                    json={"query": query},
                    headers={"Authorization": f"Apikey {SANTIMENT_KEY}"}
                )
                data = r.json()

            ts_data = data.get("data", {}).get("getMetric", {}).get("timeseriesData", [])
            if ts_data:
                latest = ts_data[-1]["value"]
                prev   = ts_data[0]["value"] if len(ts_data) > 1 else latest
                change = ((latest - prev) / prev * 100) if prev > 0 else 0
            else:
                latest, change = 0, 0

            result = {
                "coin":           coin,
                "social_volume":  latest,
                "change_24h_pct": round(change, 1),
                "source":         "santiment",
            }
            await Cache.set(cache_key, result, ttl=1800)
            return result

        except Exception as e:
            logger.warning(f"Santiment error: {e}")
            return {"coin": coin, "social_volume": 0, "source": "error"}


# ════════════════════════════════════════════════════════════════════
# 4. NEWS AGGREGATOR (المحلل المركزي)
# ════════════════════════════════════════════════════════════════════

class NewsAggregator:
    """يجمع كل مصادر الأخبار ويحللها"""

    @staticmethod
    async def get_market_summary() -> dict:
        """ملخص شامل لأخبار السوق"""
        cache_key = Cache.make_key("news_summary", "market")
        cached = await Cache.get(cache_key)
        if cached:
            return cached

        # جلب كل المصادر بالتوازي
        hot_news, rss_news = await asyncio.gather(
            CryptoPanicSource.get_news(filter="hot", limit=15),
            RSSSource.get_all_feeds(limit_per_source=5),
            return_exceptions=True
        )

        hot_news  = hot_news  if isinstance(hot_news, list)  else []
        rss_news  = rss_news  if isinstance(rss_news, list)  else []

        # حساب معنويات السوق
        all_news = hot_news + rss_news
        bullish_count = sum(1 for n in hot_news if n.get("sentiment") == "bullish")
        bearish_count = sum(1 for n in hot_news if n.get("sentiment") == "bearish")
        total         = bullish_count + bearish_count

        if total > 0:
            bull_ratio = bullish_count / total
            market_sentiment = "bullish" if bull_ratio > 0.6 else "bearish" if bull_ratio < 0.4 else "neutral"
        else:
            market_sentiment = "neutral"

        result = {
            "total_articles":    len(all_news),
            "hot_articles":      hot_news[:10],
            "market_sentiment":  market_sentiment,
            "bullish_ratio":     round(bullish_count / total * 100, 1) if total > 0 else 50,
            "top_mentioned":     NewsAggregator._extract_top_coins(hot_news),
            "ts":                datetime.utcnow().isoformat(),
        }

        await Cache.set(cache_key, result, ttl=600)
        return result

    @staticmethod
    async def get_coin_sentiment(symbol: str) -> dict:
        """معنويات عملة محددة من كل المصادر"""
        coin = symbol.split("/")[0]

        news, social = await asyncio.gather(
            CryptoPanicSource.get_coin_news(symbol),
            SantimentSource.get_social_volume(coin.lower()),
            return_exceptions=True
        )

        news   = news   if isinstance(news, list) else []
        social = social if isinstance(social, dict) else {}

        bullish = sum(1 for n in news if n.get("sentiment") == "bullish")
        bearish = sum(1 for n in news if n.get("sentiment") == "bearish")
        total   = bullish + bearish

        return {
            "symbol":          symbol,
            "news_count":      len(news),
            "news_sentiment":  "bullish" if (total > 0 and bullish/total > 0.6)
                               else "bearish" if (total > 0 and bullish/total < 0.4)
                               else "neutral",
            "social_volume":   social.get("social_volume", 0),
            "social_change":   social.get("change_24h_pct", 0),
            "recent_headlines": [n["title"] for n in news[:3]],
            "ts":              datetime.utcnow().isoformat(),
        }

    @staticmethod
    def _extract_top_coins(news: list) -> list:
        """استخراج أكثر العملات ذكراً في الأخبار"""
        from collections import Counter
        all_coins = []
        for item in news:
            all_coins.extend(item.get("currencies", []))
        return [coin for coin, _ in Counter(all_coins).most_common(5) if coin]
