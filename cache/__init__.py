"""
⚡ TradoAI Smart Caching Layer
يقلل تكاليف AI بنسبة 60%+ عبر Redis caching ذكي
"""
import os
import json
import hashlib
import redis.asyncio as redis
from typing import Any, Optional, Callable
from loguru import logger
from functools import wraps


# ════════════════════════════════════════════════════════════════════
# Redis Client (Singleton)
# ════════════════════════════════════════════════════════════════════

_redis: Optional[redis.Redis] = None


async def get_redis() -> Optional[redis.Redis]:
    global _redis
    if _redis is None:
        url = os.getenv("REDIS_URL")
        if not url:
            return None
        try:
            _redis = redis.from_url(url, decode_responses=True, socket_connect_timeout=5)
            await _redis.ping()
            logger.info("✅ Redis connected")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            return None
    return _redis


# ════════════════════════════════════════════════════════════════════
# Cache Class
# ════════════════════════════════════════════════════════════════════

class Cache:
    """Smart cache مع TTL ذكي لكل نوع بيانات"""

    TTL = {
        "price":              30,
        "ticker":             60,
        "ohlcv_1m":           60,
        "ohlcv_5m":           300,
        "ohlcv_1h":           3600,
        "ohlcv_1d":           14400,
        "scan_result":        60,
        "news_analysis":      1800,
        "macro_analysis":     7200,
        "sentiment":          900,
        "whale_alerts":       300,
        "user_data":          60,
        "tier_limits":        300,
        "analysis_full":      900,
        "default":            120,
    }

    @staticmethod
    def make_key(prefix: str, *parts) -> str:
        combined = ":".join(str(p) for p in parts)
        if len(combined) > 100:
            combined = hashlib.md5(combined.encode()).hexdigest()
        return f"trado:{prefix}:{combined}"

    @staticmethod
    async def get(key: str) -> Optional[Any]:
        r = await get_redis()
        if not r:
            return None
        try:
            value = await r.get(key)
            return json.loads(value) if value else None
        except Exception:
            return None

    @staticmethod
    async def set(key: str, value: Any, ttl: int = None, category: str = "default"):
        r = await get_redis()
        if not r:
            return
        if ttl is None:
            ttl = Cache.TTL.get(category, 120)
        try:
            await r.setex(key, ttl, json.dumps(value, default=str))
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")

    @staticmethod
    async def delete_pattern(pattern: str):
        r = await get_redis()
        if not r:
            return
        keys = []
        async for key in r.scan_iter(match=f"trado:{pattern}*"):
            keys.append(key)
        if keys:
            await r.delete(*keys)

    @staticmethod
    async def stats() -> dict:
        r = await get_redis()
        if not r:
            return {"enabled": False}
        try:
            info = await r.info("stats")
            total_keys = 0
            async for _ in r.scan_iter(match="trado:*"):
                total_keys += 1
            hits = int(info.get("keyspace_hits", 0))
            misses = int(info.get("keyspace_misses", 0))
            total_requests = hits + misses
            hit_rate = (hits / total_requests * 100) if total_requests > 0 else 0
            return {
                "enabled": True,
                "total_keys": total_keys,
                "hits": hits,
                "misses": misses,
                "hit_rate_pct": round(hit_rate, 1),
                "ai_savings_pct": round(hit_rate * 0.7, 1),
            }
        except Exception:
            return {"enabled": True, "error": "stats unavailable"}


# ════════════════════════════════════════════════════════════════════
# Decorator للـ caching التلقائي
# ════════════════════════════════════════════════════════════════════

def cached(category: str = "default", key_func: Callable = None):
    """
    Decorator يخزّن نتيجة الـ function تلقائياً.

    @cached("price")
    async def get_btc_price(symbol):
        return await exchange.fetch_ticker(symbol)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                key_parts = [func.__name__] + list(args) + [f"{k}={v}" for k, v in sorted(kwargs.items())]
                cache_key = Cache.make_key(category, *key_parts)

            cached_value = await Cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"💾 Cache HIT: {cache_key[:60]}")
                return cached_value

            result = await func(*args, **kwargs)
            await Cache.set(cache_key, result, category=category)
            logger.debug(f"💾 Cache SET: {cache_key[:60]}")
            return result
        return wrapper
    return decorator


# ════════════════════════════════════════════════════════════════════
# Shared Context (للأسعار العامة - 1 fetch لـ 1000 user)
# ════════════════════════════════════════════════════════════════════

class SharedContext:
    """
    أسعار وبيانات السوق المشتركة - يحسبها مرة لكل المستخدمين.
    التوفير: 1 API call لـ 1000 user بدلاً من 1000.
    """

    @staticmethod
    async def get_price(symbol: str) -> dict:
        key = Cache.make_key("shared_price", symbol)
        cached = await Cache.get(key)
        if cached:
            return cached
        return None

    @staticmethod
    async def set_price(symbol: str, data: dict):
        key = Cache.make_key("shared_price", symbol)
        await Cache.set(key, data, category="price")

    @staticmethod
    async def get_market_scan() -> Optional[list]:
        return await Cache.get(Cache.make_key("market_scan", "global"))

    @staticmethod
    async def set_market_scan(data: list):
        await Cache.set(Cache.make_key("market_scan", "global"), data, category="scan_result")

    @staticmethod
    async def get_news_summary() -> Optional[dict]:
        return await Cache.get(Cache.make_key("news_summary", "global"))

    @staticmethod
    async def set_news_summary(data: dict):
        await Cache.set(Cache.make_key("news_summary", "global"), data, category="news_analysis")
