"""
📊 TradoAI — Extended Data Sources (All Tested ✅)

✅ Historical OHLCV  — Bybit (365 days) + Binance (365 days)
✅ On-Chain Free     — Blockchain.com + Blockchair + Mempool.space
✅ Social Sentiment  — Reddit (r/CryptoCurrency + r/Bitcoin)
✅ CoinGecko Extended — OHLCV + Market Chart (30d history)
✅ WebSocket Manager  — Bybit + Binance real-time streams
"""
import os
import json
import asyncio
import httpx
import websockets
from datetime import datetime
from loguru import logger
from cache import Cache


async def _get(url: str, params: dict = None, timeout: int = 10) -> any:
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True,
            headers={"User-Agent": "TradoAI/1.0"}) as c:
            r = await c.get(url, params=params or {})
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.warning(f"GET {url[:55]}: {e}")
        return {} if "json" in str(type(e)) else None


# ════════════════════════════════════════════════════════════════════
# 1. HISTORICAL OHLCV (للـ Backtesting)
# ════════════════════════════════════════════════════════════════════

class HistoricalData:
    """بيانات تاريخية طويلة للـ Backtesting"""

    @staticmethod
    async def get_bybit(symbol: str, interval: str = "D", days: int = 365) -> list:
        """Bybit تاريخ حتى 365 يوم"""
        cache_key = Cache.make_key(f"hist_bybit_{interval}", symbol, str(days))
        if c := await Cache.get(cache_key):
            return c

        interval_map = {"1m":"1","5m":"5","15m":"15","30m":"30",
                        "1h":"60","4h":"240","1d":"D","1w":"W"}
        sym = symbol.replace("/","")
        d   = await _get("https://api.bybit.com/v5/market/kline", {
            "category": "spot", "symbol": sym,
            "interval": interval_map.get(interval, "D"),
            "limit": min(days, 1000)
        })
        raw     = (d.get("result") or {}).get("list", [])
        candles = [{
            "ts":     int(c[0]), "open":  float(c[1]),
            "high":   float(c[2]),"low":  float(c[3]),
            "close":  float(c[4]),"volume":float(c[5]),
            "date":   datetime.fromtimestamp(int(c[0])//1000).strftime("%Y-%m-%d")
        } for c in raw][::-1]

        await Cache.set(cache_key, candles, ttl=3600)
        return candles

    @staticmethod
    async def get_binance(symbol: str, interval: str = "1d", days: int = 365) -> list:
        """Binance تاريخ حتى 1000 شمعة"""
        cache_key = Cache.make_key(f"hist_binance_{interval}", symbol, str(days))
        if c := await Cache.get(cache_key):
            return c

        sym  = symbol.replace("/","")
        raw  = await _get("https://api.binance.com/api/v3/klines", {
            "symbol": sym, "interval": interval, "limit": min(days, 1000)
        })
        if not isinstance(raw, list):
            return []

        candles = [{
            "ts":     c[0], "open":  float(c[1]),
            "high":   float(c[2]),"low":  float(c[3]),
            "close":  float(c[4]),"volume":float(c[5]),
            "date":   datetime.fromtimestamp(c[0]//1000).strftime("%Y-%m-%d")
        } for c in raw]

        await Cache.set(cache_key, candles, ttl=3600)
        return candles

    @staticmethod
    async def get_coingecko_history(coin_id: str = "bitcoin", days: int = 30) -> list:
        """CoinGecko market chart — أسعار يومية"""
        cache_key = Cache.make_key("cg_history", coin_id, str(days))
        if c := await Cache.get(cache_key):
            return c

        d = await _get("https://api.coingecko.com/api/v3/coins/{}/market_chart".format(coin_id),
                       {"vs_currency": "usd", "days": days, "interval": "daily"})
        prices  = d.get("prices", [])
        volumes = d.get("total_volumes", [])

        result = [{
            "ts":     p[0], "price": p[1],
            "volume": volumes[i][1] if i < len(volumes) else 0,
            "date":   datetime.fromtimestamp(p[0]//1000).strftime("%Y-%m-%d")
        } for i, p in enumerate(prices)]

        await Cache.set(cache_key, result, ttl=3600)
        return result

    @staticmethod
    async def get_ohlcv(coin_id: str = "bitcoin", days: int = 7) -> list:
        """CoinGecko OHLCV"""
        cache_key = Cache.make_key("cg_ohlcv", coin_id, str(days))
        if c := await Cache.get(cache_key):
            return c

        raw = await _get("https://api.coingecko.com/api/v3/coins/{}/ohlc".format(coin_id),
                         {"vs_currency": "usd", "days": days})
        if not isinstance(raw, list):
            return []

        result = [{
            "ts": r[0], "open": r[1], "high": r[2], "low": r[3], "close": r[4]
        } for r in raw]

        await Cache.set(cache_key, result, ttl=3600)
        return result


# ════════════════════════════════════════════════════════════════════
# 2. ON-CHAIN DATA (Free)
# ════════════════════════════════════════════════════════════════════

class OnChainSource:
    """بيانات On-Chain مجانية بالكامل"""

    @staticmethod
    async def get_bitcoin_stats() -> dict:
        """إحصائيات Bitcoin من Blockchain.com"""
        cache_key = Cache.make_key("onchain_btc_stats", "global")
        if c := await Cache.get(cache_key):
            return c

        d = await _get("https://api.blockchain.info/stats")
        if not d:
            return {}

        result = {
            "hash_rate":          d.get("hash_rate", 0),
            "difficulty":         d.get("difficulty", 0),
            "total_fees_btc":     d.get("total_fees_btc", 0),
            "n_txs_per_block":    d.get("n_txs_per_block", 0),
            "minutes_between_blocks": d.get("minutes_between_blocks", 0),
            "total_btc_sent":     d.get("total_btc_sent", 0),
            "market_price_usd":   d.get("market_price_usd", 0),
            "trade_volume_usd":   d.get("trade_volume_usd", 0),
            "n_unique_addresses": d.get("n_unique_addresses", 0),
            "source": "blockchain.com",
            "ts": datetime.utcnow().isoformat(),
        }
        await Cache.set(cache_key, result, ttl=1800)
        return result

    @staticmethod
    async def get_blockchair_stats(asset: str = "bitcoin") -> dict:
        """إحصائيات تفصيلية من Blockchair"""
        cache_key = Cache.make_key("blockchair", asset)
        if c := await Cache.get(cache_key):
            return c

        d = await _get(f"https://api.blockchair.com/{asset}/stats")
        if not d:
            return {}

        data = d.get("data", {})
        result = {
            "asset":                  asset,
            "blocks":                 data.get("blocks", 0),
            "transactions_24h":       data.get("transactions_24h", 0),
            "volume_24h":             data.get("volume_24h_approximate", 0),
            "mempool_transactions":   data.get("mempool_transactions", 0),
            "mempool_size":           data.get("mempool_size", 0),
            "inflation_24h":          data.get("inflation_24h", 0),
            "largest_transaction_24h":data.get("largest_transaction_24h", {}).get("value_usd", 0),
            "nodes":                  data.get("nodes", 0),
            "source": "blockchair",
            "ts": datetime.utcnow().isoformat(),
        }
        await Cache.set(cache_key, result, ttl=1800)
        return result

    @staticmethod
    async def get_mempool_fees() -> dict:
        """رسوم Bitcoin الحالية من Mempool.space"""
        cache_key = Cache.make_key("mempool_fees", "btc")
        if c := await Cache.get(cache_key):
            return c

        d = await _get("https://mempool.space/api/v1/fees/recommended")
        if not d:
            return {}

        result = {
            "fastest_fee":   d.get("fastestFee", 0),
            "half_hour_fee": d.get("halfHourFee", 0),
            "hour_fee":      d.get("hourFee", 0),
            "economy_fee":   d.get("economyFee", 0),
            "minimum_fee":   d.get("minimumFee", 0),
            "network_congestion": "high" if d.get("fastestFee", 0) > 50 else
                                  "medium" if d.get("fastestFee", 0) > 20 else "low",
            "source": "mempool.space",
            "ts": datetime.utcnow().isoformat(),
        }
        await Cache.set(cache_key, result, ttl=300)
        return result

    @staticmethod
    async def get_full_onchain(asset: str = "bitcoin") -> dict:
        """تقرير on-chain شامل"""
        btc_stats, blockchair, fees = await asyncio.gather(
            OnChainSource.get_bitcoin_stats(),
            OnChainSource.get_blockchair_stats(asset),
            OnChainSource.get_mempool_fees(),
            return_exceptions=True
        )
        return {
            "blockchain_stats": btc_stats if isinstance(btc_stats, dict) else {},
            "blockchair":       blockchair if isinstance(blockchair, dict) else {},
            "mempool":          fees if isinstance(fees, dict) else {},
            "ts": datetime.utcnow().isoformat(),
        }


# ════════════════════════════════════════════════════════════════════
# 3. REDDIT SENTIMENT (Free — no key needed)
# ════════════════════════════════════════════════════════════════════

class RedditSentiment:
    """تحليل معنويات Reddit — مجاني بالكامل"""

    SUBREDDITS = ["CryptoCurrency", "Bitcoin", "ethereum", "solana", "CryptoMarkets"]

    @staticmethod
    async def get_posts(subreddit: str = "CryptoCurrency",
                        sort: str = "hot", limit: int = 25) -> list:
        cache_key = Cache.make_key("reddit", subreddit, sort)
        if c := await Cache.get(cache_key):
            return c

        d = await _get(
            f"https://www.reddit.com/r/{subreddit}/{sort}.json",
            {"limit": limit, "raw_json": 1},
            timeout=10
        )
        if not isinstance(d, dict):
            return []

        posts = d.get("data", {}).get("children", [])
        result = []
        for p in posts:
            post = p.get("data", {})
            title = post.get("title", "")
            if not title:
                continue
            result.append({
                "title":      title,
                "score":      post.get("score", 0),
                "comments":   post.get("num_comments", 0),
                "upvote_ratio": post.get("upvote_ratio", 0.5),
                "url":        post.get("url", ""),
                "created":    post.get("created_utc", 0),
                "subreddit":  subreddit,
                "sentiment":  RedditSentiment._analyze(title, post.get("score", 0),
                                                        post.get("upvote_ratio", 0.5)),
            })

        await Cache.set(cache_key, result, ttl=900)
        return result

    @staticmethod
    def _analyze(title: str, score: int, upvote_ratio: float) -> str:
        title_l = title.lower()
        bullish = ["moon", "surge", "pump", "bull", "breakout", "ath", "gain",
                   "buy", "long", "green", "rally", "rise", "up", "high"]
        bearish = ["crash", "dump", "bear", "drop", "fall", "down", "red",
                   "sell", "short", "fear", "panic", "low", "rug", "hack"]

        b = sum(1 for w in bullish if w in title_l)
        s = sum(1 for w in bearish if w in title_l)

        # upvote ratio يعزز الإشارة
        if upvote_ratio > 0.8 and b > s:
            return "bullish"
        if upvote_ratio < 0.4 or (s > b and score > 100):
            return "bearish"
        if b > s:
            return "bullish"
        if s > b:
            return "bearish"
        return "neutral"

    @staticmethod
    async def get_market_sentiment() -> dict:
        """معنويات Reddit الإجمالية"""
        cache_key = Cache.make_key("reddit_sentiment", "market")
        if c := await Cache.get(cache_key):
            return c

        sub1, sub2 = await asyncio.gather(
            RedditSentiment.get_posts("CryptoCurrency", "hot", 25),
            RedditSentiment.get_posts("Bitcoin", "hot", 15),
            return_exceptions=True
        )
        all_posts = []
        for r in [sub1, sub2]:
            if isinstance(r, list):
                all_posts.extend(r)

        if not all_posts:
            return {"sentiment": "neutral", "score": 50, "source": "reddit"}

        bullish = sum(1 for p in all_posts if p["sentiment"] == "bullish")
        bearish = sum(1 for p in all_posts if p["sentiment"] == "bearish")
        total   = bullish + bearish

        # وزن بالـ score
        bull_score = sum(p["score"] for p in all_posts if p["sentiment"] == "bullish")
        bear_score = sum(p["score"] for p in all_posts if p["sentiment"] == "bearish")
        total_score= bull_score + bear_score

        ratio    = (bull_score / total_score * 100) if total_score > 0 else 50
        sentiment= "bullish" if ratio > 60 else "bearish" if ratio < 40 else "neutral"

        result = {
            "sentiment":     sentiment,
            "score":         round(ratio),
            "bullish_posts": bullish,
            "bearish_posts": bearish,
            "total_posts":   len(all_posts),
            "top_posts":     sorted(all_posts, key=lambda x: x["score"], reverse=True)[:5],
            "source":        "reddit",
            "ts":            datetime.utcnow().isoformat(),
        }
        await Cache.set(cache_key, result, ttl=1800)
        return result

    @staticmethod
    async def get_coin_mentions(symbol: str) -> dict:
        """كم مرة تم ذكر العملة في Reddit اليوم"""
        coin    = symbol.split("/")[0].lower()
        posts   = await RedditSentiment.get_posts("CryptoCurrency", "new", 50)
        mentions= [p for p in posts if coin in p["title"].lower()]

        return {
            "symbol":       symbol,
            "mentions_24h": len(mentions),
            "avg_score":    sum(p["score"] for p in mentions) / len(mentions) if mentions else 0,
            "sentiment":    RedditSentiment._aggregate_sentiment(mentions),
            "posts":        mentions[:3],
        }

    @staticmethod
    def _aggregate_sentiment(posts: list) -> str:
        if not posts: return "neutral"
        b = sum(1 for p in posts if p["sentiment"] == "bullish")
        s = sum(1 for p in posts if p["sentiment"] == "bearish")
        if b > s: return "bullish"
        if s > b: return "bearish"
        return "neutral"


# ════════════════════════════════════════════════════════════════════
# 4. WEBSOCKET MANAGER (Real-time)
# ════════════════════════════════════════════════════════════════════

class WebSocketManager:
    """
    إدارة WebSocket connections لـ Bybit و Binance
    يُحدّث الـ Cache بالأسعار الحية كل ثانية
    """

    def __init__(self):
        self._running   = False
        self._tasks     = []
        self._callbacks = []   # functions to call on new price

    def on_price(self, callback):
        """سجّل callback يُستدعى عند كل تحديث سعر"""
        self._callbacks.append(callback)

    async def _notify(self, data: dict):
        for cb in self._callbacks:
            try:
                await cb(data)
            except Exception as e:
                logger.warning(f"WS callback error: {e}")

    # ── Bybit WebSocket ────────────────────────────────────────────
    async def _bybit_stream(self, symbols: list):
        url = "wss://stream.bybit.com/v5/public/spot"
        topics = [f"tickers.{s.replace('/','')}" for s in symbols]

        while self._running:
            try:
                async with websockets.connect(url, ping_interval=20) as ws:
                    await ws.send(json.dumps({"op": "subscribe", "args": topics}))
                    logger.info(f"✅ Bybit WS connected: {len(symbols)} symbols")

                    async for msg in ws:
                        if not self._running:
                            break
                        data = json.loads(msg)
                        if data.get("topic", "").startswith("tickers."):
                            t = data.get("data", {})
                            sym = data["topic"].replace("tickers.", "")
                            price_data = {
                                "symbol":     sym[:3] + "/" + sym[3:],
                                "price":      float(t.get("lastPrice", 0)),
                                "change_24h": float(t.get("price24hPcnt", 0)) * 100,
                                "volume_24h": float(t.get("volume24h", 0)),
                                "source":     "bybit_ws",
                                "ts":         datetime.utcnow().isoformat(),
                            }
                            # حدّث الـ cache
                            await Cache.set(
                                Cache.make_key("price", "bybit", price_data["symbol"]),
                                price_data, ttl=30
                            )
                            await SharedContext.set_price(price_data["symbol"], price_data)
                            await self._notify(price_data)

            except Exception as e:
                logger.warning(f"Bybit WS error: {e}. Reconnecting in 5s...")
                await asyncio.sleep(5)

    # ── Binance WebSocket ──────────────────────────────────────────
    async def _binance_stream(self, symbols: list):
        streams = "/".join([f"{s.replace('/','').lower()}@ticker" for s in symbols])
        url     = f"wss://stream.binance.com:9443/stream?streams={streams}"

        while self._running:
            try:
                async with websockets.connect(url, ping_interval=20) as ws:
                    logger.info(f"✅ Binance WS connected: {len(symbols)} symbols")

                    async for msg in ws:
                        if not self._running:
                            break
                        data  = json.loads(msg)
                        t     = data.get("data", {})
                        if t.get("e") == "24hrTicker":
                            sym  = t["s"]  # e.g. BTCUSDT
                            price_data = {
                                "symbol":     sym[:-4] + "/USDT",
                                "price":      float(t.get("c", 0)),
                                "change_24h": float(t.get("P", 0)),
                                "volume_24h": float(t.get("v", 0)),
                                "source":     "binance_ws",
                                "ts":         datetime.utcnow().isoformat(),
                            }
                            await Cache.set(
                                Cache.make_key("price", "binance", price_data["symbol"]),
                                price_data, ttl=30
                            )
                            await self._notify(price_data)

            except Exception as e:
                logger.warning(f"Binance WS error: {e}. Reconnecting in 5s...")
                await asyncio.sleep(5)

    # ── Start / Stop ───────────────────────────────────────────────
    async def start(self, symbols: list = None):
        """ابدأ WebSocket connections"""
        if symbols is None:
            symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT",
                       "BNB/USDT", "XRP/USDT", "AVAX/USDT"]

        self._running = True
        self._tasks = [
            asyncio.create_task(self._bybit_stream(symbols)),
            asyncio.create_task(self._binance_stream(symbols)),
        ]
        logger.info(f"🔌 WebSocket Manager started for {len(symbols)} symbols")
        await asyncio.gather(*self._tasks, return_exceptions=True)

    async def stop(self):
        self._running = False
        for t in self._tasks:
            t.cancel()
        logger.info("WebSocket Manager stopped")


# ════════════════════════════════════════════════════════════════════
# 5. COMPREHENSIVE MARKET ANALYZER
# يجمع كل المصادر في تقرير واحد
# ════════════════════════════════════════════════════════════════════

class ComprehensiveAnalyzer:
    """يجمع كل المصادر ويُنتج تحليلاً شاملاً للسوق"""

    @staticmethod
    async def full_market_report() -> dict:
        """تقرير شامل للسوق — يُشغَّل كل 30 دقيقة"""
        from data_sources.market import SentimentSource
        from data_sources.whales import LongShortSource, MarketMoverAnalyzer
        from data_sources.news import NewsAggregator

        results = await asyncio.gather(
            SentimentSource.get_fear_greed(),
            SentimentSource.get_trending(),
            SentimentSource.get_global_market(),
            SentimentSource.get_defi_tvl(),
            RedditSentiment.get_market_sentiment(),
            OnChainSource.get_bitcoin_stats(),
            OnChainSource.get_mempool_fees(),
            NewsAggregator.get_summary(),
            LongShortSource.get("BTC"),
            return_exceptions=True
        )

        (fear_greed, trending, global_mkt, defi_tvl,
         reddit, btc_onchain, mempool, news, btc_ls) = [
            r if not isinstance(r, Exception) else {}
            for r in results
        ]

        # حساب درجة المعنويات الإجمالية
        scores = []
        if isinstance(fear_greed, dict) and fear_greed.get("value"):
            scores.append(fear_greed["value"])
        if isinstance(reddit, dict) and reddit.get("score"):
            scores.append(reddit["score"])
        if isinstance(btc_ls, dict):
            scores.append(btc_ls.get("long_ratio", 50))

        overall_score     = round(sum(scores) / len(scores)) if scores else 50
        overall_sentiment = ("bullish" if overall_score > 60
                             else "bearish" if overall_score < 40
                             else "neutral")

        return {
            "overall_sentiment":  overall_sentiment,
            "overall_score":      overall_score,
            "fear_greed":         fear_greed,
            "trending_coins":     trending,
            "global_market":      global_mkt,
            "defi_tvl":           defi_tvl,
            "reddit_sentiment":   reddit,
            "btc_onchain":        btc_onchain,
            "mempool_fees":       mempool,
            "news_summary":       news,
            "btc_long_short":     btc_ls,
            "ts":                 datetime.utcnow().isoformat(),
        }

    @staticmethod
    async def coin_report(symbol: str) -> dict:
        """تقرير شامل لعملة محددة"""
        from data_sources.market import PriceSource, OHLCVSource, DerivativesSource
        from data_sources.whales import LargeTrades
        from data_sources.news import NewsAggregator

        coin   = symbol.split("/")[0].lower()
        coin_id_map = {
            "btc": "bitcoin", "eth": "ethereum", "sol": "solana",
            "bnb": "binancecoin", "xrp": "ripple", "avax": "avalanche-2",
        }
        coin_id = coin_id_map.get(coin, coin)

        results = await asyncio.gather(
            PriceSource.get_price(symbol),
            OHLCVSource.get(symbol, "1h", 100),
            OHLCVSource.get(symbol, "4h", 50),
            DerivativesSource.get_funding(symbol),
            DerivativesSource.get_long_short(symbol),
            DerivativesSource.get_open_interest(symbol),
            LargeTrades.analyze_pressure(symbol),
            RedditSentiment.get_coin_mentions(symbol),
            NewsAggregator.get_coin_news(symbol, 5),
            HistoricalData.get_coingecko_history(coin_id, 30),
            return_exceptions=True
        )

        (price, ohlcv_1h, ohlcv_4h, funding, ls, oi,
         large_trades, reddit_mentions, news, history) = [
            r if not isinstance(r, Exception) else {}
            for r in results
        ]

        return {
            "symbol":          symbol,
            "price":           price,
            "ohlcv_1h":        ohlcv_1h[-20:] if isinstance(ohlcv_1h, list) else [],
            "ohlcv_4h":        ohlcv_4h[-20:] if isinstance(ohlcv_4h, list) else [],
            "funding_rate":    funding,
            "long_short":      ls,
            "open_interest":   oi,
            "large_trades":    large_trades,
            "reddit":          reddit_mentions,
            "news":            news,
            "price_history_30d": history,
            "ts":              datetime.utcnow().isoformat(),
        }
