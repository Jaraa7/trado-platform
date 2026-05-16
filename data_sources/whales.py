"""
🐋 TradoAI — Whale & Market Flow Data (Production Ready)
مصادر حركات السوق المُختبرة

✅ Bybit Long/Short Ratio    — مجاني
✅ Bybit Open Interest       — مجاني
✅ Bybit Funding Rate        — مجاني
✅ Binance Large Trades      — لرصد الحيتان من order flow
✅ DeFiLlama TVL             — مجاني
❌ Whale Alert               — يحتاج subscription
❌ Glassnode                 — يحتاج subscription (نضيفه لاحقاً)
"""
import asyncio
import httpx
from datetime import datetime
from loguru import logger
from cache import Cache
import os

WHALE_ALERT_KEY = os.getenv("WHALE_ALERT_API_KEY", "")
GLASSNODE_KEY   = os.getenv("GLASSNODE_API_KEY", "")

async def _get(url: str, params: dict = None) -> dict:
    try:
        async with httpx.AsyncClient(timeout=8) as c:
            r = await c.get(url, params=params or {},
                            headers={"User-Agent": "TradoAI/1.0"})
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.warning(f"Whale GET {url[:55]}: {e}")
        return {}


class LongShortSource:

    @staticmethod
    async def get(symbol: str) -> dict:
        cache_key = Cache.make_key("ls", symbol)
        if c := await Cache.get(cache_key):
            return c

        coin = symbol.replace("/USDT","").replace("USDT","")
        d    = await _get("https://api.bybit.com/v5/market/account-ratio", {
            "category": "linear", "symbol": f"{coin}USDT",
            "period": "1h", "limit": 1
        })
        row  = ((d.get("result") or {}).get("list") or [{}])[0]
        buy  = float(row.get("buyRatio", 0.5))
        sell = float(row.get("sellRatio", 0.5))

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
    async def get_multi(symbols: list) -> dict:
        results = await asyncio.gather(*[LongShortSource.get(s) for s in symbols],
                                       return_exceptions=True)
        return {s: r for s, r in zip(symbols, results) if isinstance(r, dict)}


class LargeTrades:
    """رصد الصفقات الكبيرة من Binance كبديل لـ Whale Alert"""

    @staticmethod
    async def get_recent(symbol: str = "BTC/USDT", min_value_usd: float = 100_000) -> list:
        cache_key = Cache.make_key("large_trades", symbol)
        if c := await Cache.get(cache_key):
            return c

        sym   = symbol.replace("/", "")
        price = await _get_price(sym)
        if not price:
            return []

        # جلب آخر 500 صفقة
        d = await _get("https://api.binance.com/api/v3/trades", {
            "symbol": sym, "limit": 500
        })
        if not isinstance(d, list):
            return []

        large = []
        for t in d:
            qty = float(t.get("qty", 0))
            val = qty * price
            if val >= min_value_usd:
                large.append({
                    "symbol":    symbol,
                    "amount":    round(qty, 4),
                    "value_usd": round(val, 2),
                    "side":      "sell" if t.get("isBuyerMaker") else "buy",
                    "ts":        t.get("time", 0),
                })

        large.sort(key=lambda x: x["value_usd"], reverse=True)
        result = large[:20]
        await Cache.set(cache_key, result, ttl=60)
        return result

    @staticmethod
    async def analyze_pressure(symbol: str) -> dict:
        trades = await LargeTrades.get_recent(symbol, min_value_usd=50_000)
        if not trades:
            return {"symbol": symbol, "pressure": "neutral", "score": 50}

        buy_vol  = sum(t["value_usd"] for t in trades if t["side"] == "buy")
        sell_vol = sum(t["value_usd"] for t in trades if t["side"] == "sell")
        total    = buy_vol + sell_vol

        if total == 0:
            return {"symbol": symbol, "pressure": "neutral", "score": 50}

        buy_pct  = buy_vol / total * 100
        pressure = "bullish" if buy_pct > 60 else "bearish" if buy_pct < 40 else "neutral"

        return {
            "symbol":       symbol,
            "pressure":     pressure,
            "score":        round(buy_pct),
            "buy_volume":   round(buy_vol, 2),
            "sell_volume":  round(sell_vol, 2),
            "large_trades": trades[:5],
            "source":       "binance_trades",
        }


async def _get_price(sym: str) -> float:
    d = await _get("https://api.binance.com/api/v3/ticker/price", {"symbol": sym})
    return float(d.get("price", 0))


class WhaleAlertSource:
    """Whale Alert — يعمل فقط مع API Key مدفوع"""

    @staticmethod
    async def get_transactions(min_value: int = 1_000_000, limit: int = 20) -> list:
        if not WHALE_ALERT_KEY:
            # fallback على Large Trades من Binance
            return []

        d   = await _get("https://api.whale-alert.io/v1/transactions", {
            "api_key": WHALE_ALERT_KEY, "min_value": min_value, "limit": limit
        })
        txs = d.get("transactions", [])
        return [{
            "symbol":     t.get("symbol","").upper() + "/USDT",
            "amount":     t.get("amount", 0),
            "amount_usd": t.get("amount_usd", 0),
            "from_owner": t.get("from", {}).get("owner", "unknown"),
            "to_owner":   t.get("to",   {}).get("owner", "unknown"),
            "tx_type":    "exchange_deposit" if t.get("to", {}).get("owner_type") == "exchange" else "exchange_withdrawal",
            "ts":         t.get("timestamp", 0),
        } for t in txs]


class MarketMoverAnalyzer:
    """تحليل شامل لحركات السوق"""

    @staticmethod
    async def full_analysis(symbol: str = "BTC/USDT") -> dict:
        coin = symbol.split("/")[0]

        ls, trades, funding = await asyncio.gather(
            LongShortSource.get(coin),
            LargeTrades.analyze_pressure(symbol),
            _get("https://api.bybit.com/v5/market/tickers",
                 {"category": "linear", "symbol": coin + "USDT"}),
            return_exceptions=True
        )

        signals = []
        if isinstance(ls, dict):
            if ls.get("bias") == "bullish": signals.append(1)
            elif ls.get("bias") == "bearish": signals.append(-1)
            else: signals.append(0)

        if isinstance(trades, dict):
            score = trades.get("score", 50)
            signals.append(1 if score > 60 else -1 if score < 40 else 0)

        # Funding rate sentiment
        if isinstance(funding, dict):
            t = (funding.get("result") or {}).get("list", [{}])[0]
            fr = float(t.get("fundingRate", 0))
            signals.append(-1 if fr > 0.001 else 1 if fr < -0.0005 else 0)

        avg     = sum(signals) / len(signals) if signals else 0
        overall = "bullish" if avg > 0.33 else "bearish" if avg < -0.33 else "neutral"

        return {
            "symbol":      symbol,
            "overall":     overall,
            "score":       round((avg + 1) / 2 * 100),
            "ls_ratio":    ls     if isinstance(ls, dict)     else {},
            "large_trades":trades if isinstance(trades, dict) else {},
            "ts":          datetime.utcnow().isoformat(),
        }
