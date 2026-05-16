"""
📊 TradoAI — Market Data Sources
مصادر البيانات السوقية الحقيقية

المصادر المدعومة:
- Bybit (Spot + Futures + Perpetuals)
- Binance (Spot + Futures)
- OKX (Spot + Futures + Swap)
- CoinGecko (Prices + Market Cap + Trending)
- CryptoCompare (OHLCV تاريخي)
- Coinglass (Open Interest + Liquidations + Funding)
- Alternative.me (Fear & Greed Index)
"""
import os
import asyncio
import httpx
from typing import Optional
from datetime import datetime, timedelta
from loguru import logger
from cache import Cache, SharedContext


# ─── API Keys ─────────────────────────────────────────────────────
COINGECKO_KEY    = os.getenv("COINGECKO_API_KEY", "")
CRYPTOCOMPARE_KEY= os.getenv("CRYPTOCOMPARE_API_KEY", "")
COINGLASS_KEY    = os.getenv("COINGLASS_API_KEY", "")
BYBIT_KEY        = os.getenv("BYBIT_API_KEY", "")
BINANCE_KEY      = os.getenv("BINANCE_API_KEY", "")
OKX_KEY          = os.getenv("OKX_API_KEY", "")


# ─── HTTP Client ──────────────────────────────────────────────────
async def _get(url: str, headers: dict = None, params: dict = None, timeout=10) -> dict:
    try:
        async with httpx.AsyncClient(timeout=timeout) as c:
            r = await c.get(url, headers=headers or {}, params=params or {})
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.warning(f"HTTP GET failed: {url} → {e}")
        return {}


# ════════════════════════════════════════════════════════════════════
# 1. PRICE DATA
# ════════════════════════════════════════════════════════════════════

class PriceSource:

    @staticmethod
    async def get_price(symbol: str, exchange: str = "bybit") -> dict:
        """سعر لحظي من المنصة المختارة"""
        cache_key = Cache.make_key("price", exchange, symbol)
        cached = await Cache.get(cache_key)
        if cached:
            return cached

        symbol_clean = symbol.replace("/", "")

        if exchange == "bybit":
            data = await _get(f"https://api.bybit.com/v5/market/tickers",
                              params={"category": "spot", "symbol": symbol_clean})
            ticker = data.get("result", {}).get("list", [{}])[0]
            result = {
                "symbol": symbol,
                "price": float(ticker.get("lastPrice", 0)),
                "change_24h": float(ticker.get("price24hPcnt", 0)) * 100,
                "volume_24h": float(ticker.get("volume24h", 0)),
                "high_24h": float(ticker.get("highPrice24h", 0)),
                "low_24h": float(ticker.get("lowPrice24h", 0)),
                "source": "bybit",
                "ts": datetime.utcnow().isoformat(),
            }

        elif exchange == "binance":
            data = await _get(f"https://api.binance.com/api/v3/ticker/24hr",
                              params={"symbol": symbol_clean})
            result = {
                "symbol": symbol,
                "price": float(data.get("lastPrice", 0)),
                "change_24h": float(data.get("priceChangePercent", 0)),
                "volume_24h": float(data.get("volume", 0)),
                "high_24h": float(data.get("highPrice", 0)),
                "low_24h": float(data.get("lowPrice", 0)),
                "source": "binance",
                "ts": datetime.utcnow().isoformat(),
            }

        elif exchange == "okx":
            inst_id = symbol.replace("/", "-")
            data = await _get(f"https://www.okx.com/api/v5/market/ticker",
                              params={"instId": inst_id})
            t = data.get("data", [{}])[0]
            result = {
                "symbol": symbol,
                "price": float(t.get("last", 0)),
                "change_24h": 0,
                "volume_24h": float(t.get("vol24h", 0)),
                "high_24h": float(t.get("high24h", 0)),
                "low_24h": float(t.get("low24h", 0)),
                "source": "okx",
                "ts": datetime.utcnow().isoformat(),
            }
        else:
            result = await PriceSource._coingecko_price(symbol)

        await Cache.set(cache_key, result, category="price")
        await SharedContext.set_price(symbol, result)
        return result

    @staticmethod
    async def _coingecko_price(symbol: str) -> dict:
        """CoinGecko كمصدر احتياطي"""
        coin_map = {
            "BTC/USDT": "bitcoin", "ETH/USDT": "ethereum",
            "SOL/USDT": "solana",  "BNB/USDT": "binancecoin",
            "XRP/USDT": "ripple",  "AVAX/USDT": "avalanche-2",
        }
        coin_id = coin_map.get(symbol, symbol.split("/")[0].lower())
        headers = {"x-cg-demo-api-key": COINGECKO_KEY} if COINGECKO_KEY else {}
        data = await _get(
            f"https://api.coingecko.com/api/v3/simple/price",
            headers=headers,
            params={"ids": coin_id, "vs_currencies": "usd",
                    "include_24hr_change": "true", "include_24hr_vol": "true"}
        )
        info = data.get(coin_id, {})
        return {
            "symbol": symbol,
            "price": info.get("usd", 0),
            "change_24h": info.get("usd_24h_change", 0),
            "volume_24h": info.get("usd_24h_vol", 0),
            "source": "coingecko",
            "ts": datetime.utcnow().isoformat(),
        }

    @staticmethod
    async def get_multi_prices(symbols: list, exchange: str = "bybit") -> dict:
        """أسعار متعددة دفعة واحدة"""
        tasks = [PriceSource.get_price(s, exchange) for s in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {s: r for s, r in zip(symbols, results) if not isinstance(r, Exception)}


# ════════════════════════════════════════════════════════════════════
# 2. OHLCV (CANDLESTICK DATA)
# ════════════════════════════════════════════════════════════════════

class OHLCVSource:

    BYBIT_INTERVALS = {
        "1m": "1", "3m": "3", "5m": "5", "15m": "15",
        "30m": "30", "1h": "60", "4h": "240", "1d": "D", "1w": "W"
    }
    BINANCE_INTERVALS = {
        "1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m",
        "30m": "30m", "1h": "1h", "4h": "4h", "1d": "1d", "1w": "1w"
    }

    @staticmethod
    async def get_ohlcv(symbol: str, interval: str = "1h",
                        limit: int = 200, exchange: str = "bybit") -> list:
        """جلب بيانات الشموع اليابانية"""
        cache_key = Cache.make_key(f"ohlcv_{interval}", exchange, symbol)
        cached = await Cache.get(cache_key)
        if cached:
            return cached

        symbol_clean = symbol.replace("/", "")

        if exchange == "bybit":
            data = await _get(
                "https://api.bybit.com/v5/market/kline",
                params={
                    "category": "spot",
                    "symbol": symbol_clean,
                    "interval": OHLCVSource.BYBIT_INTERVALS.get(interval, "60"),
                    "limit": limit
                }
            )
            raw = data.get("result", {}).get("list", [])
            # Bybit: [timestamp, open, high, low, close, volume, turnover]
            candles = [{
                "ts": int(c[0]),
                "open":   float(c[1]),
                "high":   float(c[2]),
                "low":    float(c[3]),
                "close":  float(c[4]),
                "volume": float(c[5]),
            } for c in raw][::-1]  # reverse to chronological

        elif exchange == "binance":
            data = await _get(
                "https://api.binance.com/api/v3/klines",
                params={"symbol": symbol_clean,
                        "interval": OHLCVSource.BINANCE_INTERVALS.get(interval,"1h"),
                        "limit": limit}
            )
            candles = [{
                "ts":     c[0],
                "open":   float(c[1]),
                "high":   float(c[2]),
                "low":    float(c[3]),
                "close":  float(c[4]),
                "volume": float(c[5]),
            } for c in (data or [])]

        elif exchange == "okx":
            bar_map = {"1m":"1m","5m":"5m","15m":"15m","30m":"30m",
                       "1h":"1H","4h":"4H","1d":"1D","1w":"1W"}
            data = await _get(
                "https://www.okx.com/api/v5/market/candles",
                params={"instId": symbol.replace("/","-"),
                        "bar": bar_map.get(interval,"1H"), "limit": limit}
            )
            raw = data.get("data", [])
            candles = [{
                "ts":     int(c[0]),
                "open":   float(c[1]),
                "high":   float(c[2]),
                "low":    float(c[3]),
                "close":  float(c[4]),
                "volume": float(c[5]),
            } for c in raw][::-1]

        else:
            # CryptoCompare كمصدر احتياطي
            candles = await OHLCVSource._cryptocompare_ohlcv(symbol, interval, limit)

        ttl_map = {"1m": 60, "5m": 300, "15m": 900, "1h": 3600, "4h": 14400, "1d": 86400}
        await Cache.set(cache_key, candles, ttl=ttl_map.get(interval, 3600))
        return candles

    @staticmethod
    async def _cryptocompare_ohlcv(symbol: str, interval: str, limit: int) -> list:
        """CryptoCompare للبيانات التاريخية"""
        coin = symbol.split("/")[0]
        endpoint_map = {"1m": "histominute", "1h": "histohour", "1d": "histoday"}
        endpoint = endpoint_map.get(interval, "histohour")
        headers = {"authorization": f"Apikey {CRYPTOCOMPARE_KEY}"} if CRYPTOCOMPARE_KEY else {}
        data = await _get(
            f"https://min-api.cryptocompare.com/data/v2/{endpoint}",
            headers=headers,
            params={"fsym": coin, "tsym": "USD", "limit": limit}
        )
        raw = data.get("Data", {}).get("Data", [])
        return [{
            "ts":     r["time"] * 1000,
            "open":   r["open"],
            "high":   r["high"],
            "low":    r["low"],
            "close":  r["close"],
            "volume": r["volumefrom"],
        } for r in raw]


# ════════════════════════════════════════════════════════════════════
# 3. ORDER BOOK
# ════════════════════════════════════════════════════════════════════

class OrderBookSource:

    @staticmethod
    async def get_orderbook(symbol: str, exchange: str = "bybit",
                            depth: int = 25) -> dict:
        """Order Book مع تحليل الضغط"""
        symbol_clean = symbol.replace("/", "")

        if exchange == "bybit":
            data = await _get(
                "https://api.bybit.com/v5/market/orderbook",
                params={"category": "spot", "symbol": symbol_clean, "limit": depth}
            )
            book = data.get("result", {})
            bids = [[float(p), float(q)] for p, q in book.get("b", [])]
            asks = [[float(p), float(q)] for p, q in book.get("a", [])]

        elif exchange == "binance":
            data = await _get(
                "https://api.binance.com/api/v3/depth",
                params={"symbol": symbol_clean, "limit": depth}
            )
            bids = [[float(p), float(q)] for p, q in data.get("bids", [])]
            asks = [[float(p), float(q)] for p, q in data.get("asks", [])]
        else:
            return {}

        # تحليل الضغط
        bid_vol   = sum(b[1] for b in bids)
        ask_vol   = sum(a[1] for a in asks)
        total_vol = bid_vol + ask_vol
        pressure  = (bid_vol / total_vol * 100) if total_vol > 0 else 50

        return {
            "symbol":        symbol,
            "bids":          bids[:10],
            "asks":          asks[:10],
            "bid_volume":    round(bid_vol, 2),
            "ask_volume":    round(ask_vol, 2),
            "buy_pressure":  round(pressure, 1),
            "sell_pressure": round(100 - pressure, 1),
            "spread":        round(asks[0][0] - bids[0][0], 6) if asks and bids else 0,
            "source":        exchange,
        }


# ════════════════════════════════════════════════════════════════════
# 4. DERIVATIVES DATA (Funding + Open Interest + Liquidations)
# ════════════════════════════════════════════════════════════════════

class DerivativesSource:

    @staticmethod
    async def get_funding_rate(symbol: str) -> dict:
        """معدل التمويل للعقود الدائمة"""
        symbol_clean = symbol.replace("/", "")
        cache_key = Cache.make_key("funding", symbol_clean)
        cached = await Cache.get(cache_key)
        if cached:
            return cached

        # Bybit Perpetuals
        data = await _get(
            "https://api.bybit.com/v5/market/tickers",
            params={"category": "linear", "symbol": symbol_clean}
        )
        ticker = data.get("result", {}).get("list", [{}])[0]
        result = {
            "symbol":        symbol,
            "funding_rate":  float(ticker.get("fundingRate", 0)),
            "next_funding":  ticker.get("nextFundingTime", ""),
            "open_interest": float(ticker.get("openInterest", 0)),
            "source":        "bybit",
        }
        await Cache.set(cache_key, result, ttl=300)
        return result

    @staticmethod
    async def get_liquidations(symbol: str = "BTC") -> dict:
        """بيانات التصفيات (Coinglass)"""
        cache_key = Cache.make_key("liquidations", symbol)
        cached = await Cache.get(cache_key)
        if cached:
            return cached

        headers = {"coinglassSecret": COINGLASS_KEY} if COINGLASS_KEY else {}
        data = await _get(
            "https://open-api.coinglass.com/public/v2/liquidation_history",
            headers=headers,
            params={"symbol": symbol, "time_type": "h4"}
        )

        if not data.get("data"):
            # Bybit fallback: recent trades with large sizes
            return {"symbol": symbol, "liquidations_24h": 0, "source": "unavailable"}

        liq_data = data.get("data", {})
        result = {
            "symbol":          symbol,
            "long_liq_24h":    liq_data.get("longLiquidationUsd24h", 0),
            "short_liq_24h":   liq_data.get("shortLiquidationUsd24h", 0),
            "total_liq_24h":   liq_data.get("totalLiquidationUsd24h", 0),
            "source":          "coinglass",
        }
        await Cache.set(cache_key, result, ttl=900)
        return result

    @staticmethod
    async def get_open_interest(symbol: str = "BTC") -> dict:
        """Open Interest عبر المنصات"""
        cache_key = Cache.make_key("oi", symbol)
        cached = await Cache.get(cache_key)
        if cached:
            return cached

        symbol_clean = symbol.replace("/", "").replace("USDT", "")

        # Bybit OI
        data = await _get(
            "https://api.bybit.com/v5/market/open-interest",
            params={"category": "linear",
                    "symbol": f"{symbol_clean}USDT", "intervalTime": "1h", "limit": 1}
        )
        oi_list = data.get("result", {}).get("list", [])
        oi_value = float(oi_list[0].get("openInterest", 0)) if oi_list else 0

        result = {"symbol": symbol, "open_interest": oi_value, "source": "bybit"}
        await Cache.set(cache_key, result, ttl=300)
        return result


# ════════════════════════════════════════════════════════════════════
# 5. MARKET SENTIMENT
# ════════════════════════════════════════════════════════════════════

class SentimentSource:

    @staticmethod
    async def get_fear_greed() -> dict:
        """Fear & Greed Index"""
        cache_key = Cache.make_key("fear_greed", "global")
        cached = await Cache.get(cache_key)
        if cached:
            return cached

        data = await _get("https://api.alternative.me/fng/?limit=2")
        items = data.get("data", [])
        if not items:
            return {"value": 50, "label": "Neutral", "source": "alternative.me"}

        current = items[0]
        prev    = items[1] if len(items) > 1 else current
        result  = {
            "value":       int(current.get("value", 50)),
            "label":       current.get("value_classification", "Neutral"),
            "prev_value":  int(prev.get("value", 50)),
            "trend":       "improving" if int(current.get("value",50)) > int(prev.get("value",50)) else "declining",
            "source":      "alternative.me",
            "ts":          datetime.utcnow().isoformat(),
        }
        await Cache.set(cache_key, result, ttl=3600)
        return result

    @staticmethod
    async def get_trending_coins() -> list:
        """العملات الرائجة من CoinGecko"""
        cache_key = Cache.make_key("trending", "coingecko")
        cached = await Cache.get(cache_key)
        if cached:
            return cached

        headers = {"x-cg-demo-api-key": COINGECKO_KEY} if COINGECKO_KEY else {}
        data = await _get("https://api.coingecko.com/api/v3/search/trending",
                          headers=headers)
        coins = data.get("coins", [])
        result = [{
            "name":   c["item"]["name"],
            "symbol": c["item"]["symbol"].upper() + "/USDT",
            "rank":   c["item"].get("market_cap_rank", 999),
        } for c in coins[:7]]

        await Cache.set(cache_key, result, ttl=1800)
        return result

    @staticmethod
    async def get_global_market() -> dict:
        """إحصائيات السوق العامة"""
        cache_key = Cache.make_key("global_market", "coingecko")
        cached = await Cache.get(cache_key)
        if cached:
            return cached

        headers = {"x-cg-demo-api-key": COINGECKO_KEY} if COINGECKO_KEY else {}
        data = await _get("https://api.coingecko.com/api/v3/global",
                          headers=headers)
        d = data.get("data", {})
        result = {
            "total_market_cap_usd": d.get("total_market_cap", {}).get("usd", 0),
            "total_volume_24h":     d.get("total_volume", {}).get("usd", 0),
            "btc_dominance":        round(d.get("market_cap_percentage", {}).get("btc", 0), 1),
            "eth_dominance":        round(d.get("market_cap_percentage", {}).get("eth", 0), 1),
            "market_cap_change_24h":d.get("market_cap_change_percentage_24h_usd", 0),
            "active_coins":         d.get("active_cryptocurrencies", 0),
            "source": "coingecko",
        }
        await Cache.set(cache_key, result, ttl=1800)
        return result
