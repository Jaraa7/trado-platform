"""
🐋 TradoAI — Whale & On-Chain Data Sources
تتبع حركات الحيتان وبيانات الـ On-Chain

المصادر:
- Whale Alert API (تحويلات الحيتان الكبيرة)
- Glassnode (On-chain metrics)
- CryptoQuant (Exchange flows)
- Coinglass (Long/Short Ratio)
- DeFiLlama (TVL)
- Bybit Large Trades (تتبع الصفقات الكبيرة)
"""
import os
import asyncio
import httpx
from datetime import datetime
from loguru import logger
from cache import Cache


WHALE_ALERT_KEY  = os.getenv("WHALE_ALERT_API_KEY", "")
GLASSNODE_KEY    = os.getenv("GLASSNODE_API_KEY", "")
CRYPTOQUANT_KEY  = os.getenv("CRYPTOQUANT_API_KEY", "")
COINGLASS_KEY    = os.getenv("COINGLASS_API_KEY", "")


async def _get(url: str, headers: dict = None, params: dict = None) -> dict:
    try:
        async with httpx.AsyncClient(timeout=12) as c:
            r = await c.get(url, headers=headers or {}, params=params or {})
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.warning(f"Whale data fetch: {url[:60]} → {e}")
        return {}


# ════════════════════════════════════════════════════════════════════
# 1. WHALE ALERT
# ════════════════════════════════════════════════════════════════════

class WhaleAlertSource:
    BASE = "https://api.whale-alert.io/v1"

    @staticmethod
    async def get_transactions(min_value: int = 1_000_000,
                               limit: int = 20,
                               currencies: list = None) -> list:
        """تحويلات الحيتان (≥ $1M افتراضياً)"""
        if not WHALE_ALERT_KEY:
            return WhaleAlertSource._mock_transactions()

        cache_key = Cache.make_key("whale_txs", str(min_value))
        cached = await Cache.get(cache_key)
        if cached:
            return cached

        params = {
            "api_key": WHALE_ALERT_KEY,
            "min_value": min_value,
            "limit": limit,
        }
        if currencies:
            params["currency"] = ",".join(currencies)

        data = await _get(f"{WhaleAlertSource.BASE}/transactions", params=params)
        txs  = data.get("transactions", [])

        result = [{
            "id":           t.get("id"),
            "blockchain":   t.get("blockchain", ""),
            "symbol":       t.get("symbol", "").upper() + "/USDT",
            "amount":       t.get("amount", 0),
            "amount_usd":   t.get("amount_usd", 0),
            "from_owner":   t.get("from", {}).get("owner", "unknown"),
            "to_owner":     t.get("to", {}).get("owner", "unknown"),
            "from_type":    t.get("from", {}).get("owner_type", "unknown"),
            "to_type":      t.get("to", {}).get("owner_type", "unknown"),
            "tx_type":      WhaleAlertSource._classify_tx(t),
            "timestamp":    t.get("timestamp", 0),
            "hash":         t.get("hash", ""),
        } for t in txs]

        await Cache.set(cache_key, result, ttl=300)
        return result

    @staticmethod
    def _classify_tx(tx: dict) -> str:
        """تصنيف نوع التحويل"""
        from_type = tx.get("from", {}).get("owner_type", "")
        to_type   = tx.get("to", {}).get("owner_type", "")

        if from_type == "exchange" and to_type == "unknown":
            return "exchange_withdrawal"   # احتمال شراء
        if from_type == "unknown" and to_type == "exchange":
            return "exchange_deposit"      # احتمال بيع
        if from_type == "exchange" and to_type == "exchange":
            return "exchange_to_exchange"  # تحركات داخلية
        if "whale" in from_type.lower() or "whale" in to_type.lower():
            return "whale_move"
        return "transfer"

    @staticmethod
    def _mock_transactions() -> list:
        """بيانات تجريبية لو لا API Key"""
        return [
            {"symbol": "BTC/USDT", "amount": 1250, "amount_usd": 130_000_000,
             "from_owner": "Coinbase", "to_owner": "Unknown Wallet",
             "tx_type": "exchange_withdrawal", "timestamp": int(datetime.utcnow().timestamp())},
            {"symbol": "ETH/USDT", "amount": 25000, "amount_usd": 65_000_000,
             "from_owner": "Unknown Wallet", "to_owner": "Binance",
             "tx_type": "exchange_deposit", "timestamp": int(datetime.utcnow().timestamp())},
        ]

    @staticmethod
    async def analyze_whale_pressure(symbol: str = "BTC/USDT") -> dict:
        """تحليل ضغط الحيتان على عملة معينة"""
        coin = symbol.split("/")[0].lower()
        txs  = await WhaleAlertSource.get_transactions(
            currencies=[coin], min_value=500_000
        )

        if not txs:
            return {"symbol": symbol, "pressure": "neutral", "score": 50}

        buy_volume  = sum(t["amount_usd"] for t in txs if t["tx_type"] == "exchange_withdrawal")
        sell_volume = sum(t["amount_usd"] for t in txs if t["tx_type"] == "exchange_deposit")
        total       = buy_volume + sell_volume

        if total == 0:
            return {"symbol": symbol, "pressure": "neutral", "score": 50}

        buy_pct  = buy_volume  / total * 100
        pressure = "bullish" if buy_pct > 60 else "bearish" if buy_pct < 40 else "neutral"
        score    = round(buy_pct)

        return {
            "symbol":       symbol,
            "pressure":     pressure,
            "score":        score,
            "buy_volume":   buy_volume,
            "sell_volume":  sell_volume,
            "recent_txs":   txs[:5],
        }


# ════════════════════════════════════════════════════════════════════
# 2. GLASSNODE (On-Chain)
# ════════════════════════════════════════════════════════════════════

class GlassnodeSource:
    BASE = "https://api.glassnode.com/v1/metrics"

    @staticmethod
    async def _fetch(endpoint: str, asset: str = "BTC") -> dict:
        if not GLASSNODE_KEY:
            return {}
        data = await _get(
            f"{GlassnodeSource.BASE}/{endpoint}",
            params={"a": asset, "api_key": GLASSNODE_KEY,
                    "i": "24h", "f": "JSON", "timestamp_format": "humanized"}
        )
        return data[-1] if isinstance(data, list) and data else {}

    @staticmethod
    async def get_exchange_flows(asset: str = "BTC") -> dict:
        """تدفقات العملات من/إلى المنصات"""
        cache_key = Cache.make_key("glassnode_flows", asset)
        cached = await Cache.get(cache_key)
        if cached:
            return cached

        inflow, outflow = await asyncio.gather(
            GlassnodeSource._fetch("transactions/transfers_volume_to_exchanges_sum", asset),
            GlassnodeSource._fetch("transactions/transfers_volume_from_exchanges_sum", asset),
        )

        result = {
            "asset":       asset,
            "exchange_inflow":  inflow.get("v", 0),
            "exchange_outflow": outflow.get("v", 0),
            "net_flow":    outflow.get("v", 0) - inflow.get("v", 0),
            "bias":        "accumulation" if outflow.get("v",0) > inflow.get("v",0) else "distribution",
            "source":      "glassnode",
        }

        await Cache.set(cache_key, result, ttl=3600)
        return result

    @staticmethod
    async def get_active_addresses(asset: str = "BTC") -> dict:
        """عدد العناوين النشطة"""
        cache_key = Cache.make_key("glassnode_active", asset)
        cached = await Cache.get(cache_key)
        if cached:
            return cached

        data = await GlassnodeSource._fetch("addresses/active_count", asset)
        result = {
            "asset":            asset,
            "active_addresses": data.get("v", 0),
            "source":           "glassnode",
        }
        await Cache.set(cache_key, result, ttl=3600)
        return result


# ════════════════════════════════════════════════════════════════════
# 3. LONG/SHORT RATIO (Coinglass)
# ════════════════════════════════════════════════════════════════════

class LongShortSource:

    @staticmethod
    async def get_ratio(symbol: str = "BTC") -> dict:
        """نسبة Long/Short عبر المنصات"""
        cache_key = Cache.make_key("ls_ratio", symbol)
        cached = await Cache.get(cache_key)
        if cached:
            return cached

        coin = symbol.replace("/USDT", "").replace("USDT", "")

        # Bybit Top Traders Long/Short
        data = await _get(
            "https://api.bybit.com/v5/market/account-ratio",
            params={"category": "linear", "symbol": f"{coin}USDT",
                    "period": "1h", "limit": 1}
        )
        ratio_list = data.get("result", {}).get("list", [{}])
        ratio      = ratio_list[0] if ratio_list else {}

        buy_ratio  = float(ratio.get("buyRatio", 0.5))
        sell_ratio = float(ratio.get("sellRatio", 0.5))

        result = {
            "symbol":      coin + "/USDT",
            "long_ratio":  round(buy_ratio * 100, 1),
            "short_ratio": round(sell_ratio * 100, 1),
            "bias":        "bullish" if buy_ratio > 0.55 else "bearish" if buy_ratio < 0.45 else "neutral",
            "source":      "bybit",
        }

        await Cache.set(cache_key, result, ttl=300)
        return result

    @staticmethod
    async def get_multi_ratio(symbols: list) -> dict:
        """نسب Long/Short لعدة عملات"""
        tasks  = [LongShortSource.get_ratio(s) for s in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {s: r for s, r in zip(symbols, results) if isinstance(r, dict)}


# ════════════════════════════════════════════════════════════════════
# 4. DEFI & TVL
# ════════════════════════════════════════════════════════════════════

class DeFiSource:

    @staticmethod
    async def get_total_tvl() -> dict:
        """إجمالي TVL في DeFi (DeFiLlama)"""
        cache_key = Cache.make_key("defi_tvl", "total")
        cached = await Cache.get(cache_key)
        if cached:
            return cached

        data = await _get("https://api.llama.fi/v2/charts")
        if isinstance(data, list) and data:
            latest = data[-1]
            prev   = data[-2] if len(data) > 1 else data[-1]
            change = (latest["totalLiquidityUSD"] - prev["totalLiquidityUSD"]) / prev["totalLiquidityUSD"] * 100

            result = {
                "tvl_usd":      latest["totalLiquidityUSD"],
                "change_24h":   round(change, 2),
                "source":       "defillama",
                "ts":           datetime.utcnow().isoformat(),
            }
            await Cache.set(cache_key, result, ttl=3600)
            return result
        return {"tvl_usd": 0, "source": "unavailable"}


# ════════════════════════════════════════════════════════════════════
# 5. MARKET MOVER (المحلل المركزي)
# ════════════════════════════════════════════════════════════════════

class MarketMoverAnalyzer:
    """يجمع كل مصادر حركات السوق ويعطي صورة شاملة"""

    @staticmethod
    async def full_analysis(symbol: str = "BTC/USDT") -> dict:
        """تحليل كامل لحركات السوق لعملة معينة"""
        coin = symbol.split("/")[0]

        whale, ls_ratio, flows = await asyncio.gather(
            WhaleAlertSource.analyze_whale_pressure(symbol),
            LongShortSource.get_ratio(coin),
            GlassnodeSource.get_exchange_flows(coin),
            return_exceptions=True
        )

        # إعطاء درجة للسوق
        signals = []
        if isinstance(whale, dict):
            if whale.get("pressure") == "bullish":   signals.append(1)
            elif whale.get("pressure") == "bearish":  signals.append(-1)
            else:                                      signals.append(0)

        if isinstance(ls_ratio, dict):
            if ls_ratio.get("bias") == "bullish":    signals.append(1)
            elif ls_ratio.get("bias") == "bearish":   signals.append(-1)
            else:                                      signals.append(0)

        if isinstance(flows, dict):
            if flows.get("bias") == "accumulation":  signals.append(1)
            elif flows.get("bias") == "distribution": signals.append(-1)
            else:                                      signals.append(0)

        avg = sum(signals) / len(signals) if signals else 0
        overall = "bullish" if avg > 0.33 else "bearish" if avg < -0.33 else "neutral"

        return {
            "symbol":        symbol,
            "overall":       overall,
            "score":         round((avg + 1) / 2 * 100),
            "whale_data":    whale    if isinstance(whale, dict)    else {},
            "ls_ratio":      ls_ratio if isinstance(ls_ratio, dict) else {},
            "onchain_flows": flows    if isinstance(flows, dict)    else {},
            "ts":            datetime.utcnow().isoformat(),
        }
