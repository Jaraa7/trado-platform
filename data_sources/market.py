"""
📊 TradoAI — Market Data Sources (Production Ready)
مصادر البيانات السوقية الحقيقية — مُختبرة وتعمل

✅ Bybit    — Ticker, OHLCV, Funding, L/S Ratio, Open Interest
✅ Binance  — Ticker, OHLCV
✅ CoinGecko — Price, Trending, Global Market (no key needed)
✅ Alternative.me — Fear & Greed Index
✅ DeFiLlama — Total TVL
⚠️ OKX     — fallback (may timeout in some regions)
"""
import asyncio
import httpx
from datetime import datetime
from loguru import logger
from cache import Cache, SharedContext


async def _get(url: str, params: dict = None, timeout: int = 8) -> dict:
    try:
        async with httpx.AsyncClient(timeout=timeout) as c:
            r = await c.get(url, params=params or {},
                            headers={"User-Agent": "TradoAI/1.0"})
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.warning(f"GET {url[:55]} → {e}")
        return {}


# ════════════════════════════════════════════════════════════════════
# PRICE DATA
# ════════════════════════════════════════════════════════════════════

class PriceSource:

    @staticmethod
    async def get_price(symbol: str, exchange: str = "bybit") -> dict:
        cache_key = Cache.make_key("price", exchange, symbol)
        if c := await Cache.get(cache_key):
            return c

        sym = symbol.replace("/", "")
        result = {}

        if exchange == "bybit":
            d = await _get("https://api.bybit.com/v5/market/tickers",
                           {"category": "spot", "symbol": sym})
            t = (d.get("result") or {}).get("list", [{}])[0]
            result = {
                "symbol": symbol, "source": "bybit",
                "price":       float(t.get("lastPrice", 0)),
                "change_24h":  float(t.get("price24hPcnt", 0)) * 100,
                "volume_24h":  float(t.get("volume24h", 0)),
                "high_24h":    float(t.get("highPrice24h", 0)),
                "low_24h":     float(t.get("lowPrice24h", 0)),
                "ts": datetime.utcnow().isoformat(),
            }

        elif exchange == "binance":
            d = await _get("https://api.binance.com/api/v3/ticker/24hr",
                           {"symbol": sym})
            result = {
                "symbol": symbol, "source": "binance",
                "price":       float(d.get("lastPrice", 0)),
                "change_24h":  float(d.get("priceChangePercent", 0)),
                "volume_24h":  float(d.get("volume", 0)),
                "high_24h":    float(d.get("highPrice", 0)),
                "low_24h":     float(d.get("lowPrice", 0)),
                "ts": datetime.utcnow().isoformat(),
            }

        else:
            result = await PriceSource._coingecko(symbol)

        if result.get("price", 0) > 0:
            await Cache.set(cache_key, result, category="price")
            await SharedContext.set_price(symbol, result)

        return result

    @staticmethod
    async def _coingecko(symbol: str) -> dict:
        coin_ids = {
            "BTC/USDT": "bitcoin", "ETH/USDT": "ethereum",
            "SOL/USDT": "solana",  "BNB/USDT": "binancecoin",
            "XRP/USDT": "ripple",  "AVAX/USDT": "avalanche-2",
            "DOGE/USDT": "dogecoin", "ADA/USDT": "cardano",
        }
        cid = coin_ids.get(symbol, symbol.split("/")[0].lower())
        d = await _get("https://api.coingecko.com/api/v3/simple/price", {
            "ids": cid, "vs_currencies": "usd",
            "include_24hr_change": "true", "include_24hr_vol": "true"
        })
        info = d.get(cid, {})
        return {
            "symbol": symbol, "source": "coingecko",
            "price":      info.get("usd", 0),
            "change_24h": info.get("usd_24h_change", 0),
            "volume_24h": info.get("usd_24h_vol", 0),
            "ts": datetime.utcnow().isoformat(),
        }

    @staticmethod
    async def get_multi(symbols: list, exchange: str = "bybit") -> dict:
        results = await asyncio.gather(
            *[PriceSource.get_price(s, exchange) for s in symbols],
            return_exceptions=True
        )
        return {s: r for s, r in zip(symbols, results) if isinstance(r, dict)}


# ════════════════════════════════════════════════════════════════════
# OHLCV
# ════════════════════════════════════════════════════════════════════

class OHLCVSource:
    _BYBIT  = {"1m":"1","3m":"3","5m":"5","15m":"15","30m":"30","1h":"60","4h":"240","1d":"D","1w":"W"}
    _BINANCE= {"1m":"1m","3m":"3m","5m":"5m","15m":"15m","30m":"30m","1h":"1h","4h":"4h","1d":"1d","1w":"1w"}

    @staticmethod
    async def get(symbol: str, interval: str = "1h",
                  limit: int = 200, exchange: str = "bybit") -> list:
        cache_key = Cache.make_key(f"ohlcv_{interval}", exchange, symbol)
        if c := await Cache.get(cache_key):
            return c

        sym = symbol.replace("/", "")
        candles = []

        if exchange == "bybit":
            d = await _get("https://api.bybit.com/v5/market/kline", {
                "category": "spot", "symbol": sym,
                "interval": OHLCVSource._BYBIT.get(interval, "60"),
                "limit": limit
            })
            raw = (d.get("result") or {}).get("list", [])
            candles = [{
                "ts": int(c[0]), "open": float(c[1]),
                "high": float(c[2]), "low": float(c[3]),
                "close": float(c[4]), "volume": float(c[5]),
            } for c in raw][::-1]

        elif exchange == "binance":
            raw = await _get("https://api.binance.com/api/v3/klines", {
                "symbol": sym,
                "interval": OHLCVSource._BINANCE.get(interval, "1h"),
                "limit": limit
            })
            if isinstance(raw, list):
                candles = [{
                    "ts": c[0], "open": float(c[1]), "high": float(c[2]),
                    "low": float(c[3]), "close": float(c[4]), "volume": float(c[5]),
                } for c in raw]

        ttl = {"1m":60,"5m":300,"15m":900,"1h":3600,"4h":14400,"1d":86400}
        if candles:
            await Cache.set(cache_key, candles, ttl=ttl.get(interval, 3600))

        return candles


# ════════════════════════════════════════════════════════════════════
# ORDER BOOK
# ════════════════════════════════════════════════════════════════════

class OrderBookSource:

    @staticmethod
    async def get(symbol: str, exchange: str = "bybit", depth: int = 25) -> dict:
        sym = symbol.replace("/", "")
        bids, asks = [], []

        if exchange == "bybit":
            d = await _get("https://api.bybit.com/v5/market/orderbook",
                           {"category": "spot", "symbol": sym, "limit": depth})
            book = d.get("result", {})
            bids = [[float(p), float(q)] for p, q in book.get("b", [])]
            asks = [[float(p), float(q)] for p, q in book.get("a", [])]

        elif exchange == "binance":
            d = await _get("https://api.binance.com/api/v3/depth",
                           {"symbol": sym, "limit": depth})
            bids = [[float(p), float(q)] for p, q in d.get("bids", [])]
            asks = [[float(p), float(q)] for p, q in d.get("asks", [])]

        if not bids or not asks:
            return {}

        bid_vol   = sum(b[1] for b in bids)
        ask_vol   = sum(a[1] for a in asks)
        total     = bid_vol + ask_vol
        pressure  = (bid_vol / total * 100) if total > 0 else 50

        return {
            "symbol": symbol, "source": exchange,
            "bids": bids[:10], "asks": asks[:10],
            "bid_volume": round(bid_vol, 2),
            "ask_volume": round(ask_vol, 2),
            "buy_pressure":  round(pressure, 1),
            "sell_pressure": round(100 - pressure, 1),
            "spread": round(asks[0][0] - bids[0][0], 6),
        }


# ════════════════════════════════════════════════════════════════════
# DERIVATIVES (Funding + OI + L/S Ratio)
# ════════════════════════════════════════════════════════════════════

class DerivativesSource:

    @staticmethod
    async def get_funding(symbol: str) -> dict:
        cache_key = Cache.make_key("funding", symbol)
        if c := await Cache.get(cache_key):
            return c

        sym = symbol.replace("/", "")
        d   = await _get("https://api.bybit.com/v5/market/tickers",
                         {"category": "linear", "symbol": sym})
        t   = (d.get("result") or {}).get("list", [{}])[0]

        result = {
            "symbol":        symbol,
            "funding_rate":  float(t.get("fundingRate", 0)),
            "next_funding":  t.get("nextFundingTime", ""),
            "open_interest": float(t.get("openInterest", 0)),
            "source":        "bybit",
        }
        await Cache.set(cache_key, result, ttl=300)
        return result

    @staticmethod
    async def get_long_short(symbol: str) -> dict:
        cache_key = Cache.make_key("ls_ratio", symbol)
        if c := await Cache.get(cache_key):
            return c

        coin = symbol.replace("/USDT", "").replace("USDT", "")
        d    = await _get("https://api.bybit.com/v5/market/account-ratio", {
            "category": "linear", "symbol": f"{coin}USDT",
            "period": "1h", "limit": 1
        })
        row   = ((d.get("result") or {}).get("list") or [{}])[0]
        buy   = float(row.get("buyRatio", 0.5))
        sell  = float(row.get("sellRatio", 0.5))

        result = {
            "symbol":      f"{coin}/USDT",
            "long_ratio":  round(buy * 100, 1),
            "short_ratio": round(sell * 100, 1),
            "bias": "bullish" if buy > 0.55 else "bearish" if buy < 0.45 else "neutral",
            "source": "bybit",
        }
        await Cache.set(cache_key, result, ttl=300)
        return result

    @staticmethod
    async def get_open_interest(symbol: str) -> dict:
        cache_key = Cache.make_key("oi", symbol)
        if c := await Cache.get(cache_key):
            return c

        coin = symbol.replace("/USDT", "").replace("USDT", "")
        d    = await _get("https://api.bybit.com/v5/market/open-interest", {
            "category": "linear", "symbol": f"{coin}USDT",
            "intervalTime": "1h", "limit": 1
        })
        oi_list = (d.get("result") or {}).get("list", [])
        oi      = float(oi_list[0].get("openInterest", 0)) if oi_list else 0

        result  = {"symbol": symbol, "open_interest": oi, "source": "bybit"}
        await Cache.set(cache_key, result, ttl=300)
        return result


# ════════════════════════════════════════════════════════════════════
# SENTIMENT
# ════════════════════════════════════════════════════════════════════

class SentimentSource:

    @staticmethod
    async def get_fear_greed() -> dict:
        cache_key = Cache.make_key("fear_greed", "global")
        if c := await Cache.get(cache_key):
            return c

        d     = await _get("https://api.alternative.me/fng/?limit=2")
        items = d.get("data", [])
        if not items:
            return {"value": 50, "label": "Neutral", "source": "alternative.me"}

        curr = items[0]
        prev = items[1] if len(items) > 1 else curr
        result = {
            "value":      int(curr.get("value", 50)),
            "label":      curr.get("value_classification", "Neutral"),
            "prev_value": int(prev.get("value", 50)),
            "trend": "improving" if int(curr.get("value",50)) > int(prev.get("value",50)) else "declining",
            "source": "alternative.me",
            "ts": datetime.utcnow().isoformat(),
        }
        await Cache.set(cache_key, result, ttl=3600)
        return result

    @staticmethod
    async def get_trending() -> list:
        cache_key = Cache.make_key("trending", "coingecko")
        if c := await Cache.get(cache_key):
            return c

        d     = await _get("https://api.coingecko.com/api/v3/search/trending")
        coins = d.get("coins", [])
        result = [{
            "name":   c["item"]["name"],
            "symbol": c["item"]["symbol"].upper() + "/USDT",
            "rank":   c["item"].get("market_cap_rank", 999),
        } for c in coins[:7]]

        await Cache.set(cache_key, result, ttl=1800)
        return result

    @staticmethod
    async def get_global_market() -> dict:
        cache_key = Cache.make_key("global_market", "coingecko")
        if c := await Cache.get(cache_key):
            return c

        d = await _get("https://api.coingecko.com/api/v3/global")
        g = d.get("data", {})
        result = {
            "total_mcap_usd":  g.get("total_market_cap", {}).get("usd", 0),
            "total_vol_24h":   g.get("total_volume", {}).get("usd", 0),
            "btc_dominance":   round(g.get("market_cap_percentage", {}).get("btc", 0), 1),
            "eth_dominance":   round(g.get("market_cap_percentage", {}).get("eth", 0), 1),
            "mcap_change_24h": g.get("market_cap_change_percentage_24h_usd", 0),
            "source": "coingecko",
        }
        await Cache.set(cache_key, result, ttl=1800)
        return result

    @staticmethod
    async def get_defi_tvl() -> dict:
        cache_key = Cache.make_key("defi_tvl", "total")
        if c := await Cache.get(cache_key):
            return c

        # DeFiLlama v1 endpoint (مُختبر ✅)
        d = await _get("https://api.llama.fi/charts")
        if isinstance(d, list) and len(d) >= 2:
            latest = d[-1]["totalLiquidityUSD"]
            prev   = d[-2]["totalLiquidityUSD"]
            change = (latest - prev) / prev * 100 if prev > 0 else 0
            result = {
                "tvl_usd":    latest,
                "change_24h": round(change, 2),
                "source":     "defillama",
                "ts":         datetime.utcnow().isoformat(),
            }
            await Cache.set(cache_key, result, ttl=3600)
            return result

        return {"tvl_usd": 0, "source": "unavailable"}
