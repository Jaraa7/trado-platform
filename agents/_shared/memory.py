"""
TRADO Memory System
Short-term (Redis) + Long-term (Supabase) + Episodic memory
"""
import json
import asyncio
from typing import Any, Optional
from datetime import datetime, timedelta
from loguru import logger


class MemorySystem:
    """
    نظام ذاكرة ثلاثي الطبقات لكل agent:
    - Short-term: Redis (الجلسة الحالية)
    - Long-term:  Supabase (تاريخ كامل)
    - Episodic:   نجاحات وإخفاقات للتعلم
    """

    def __init__(self, agent_id: str, user_id: str):
        self.agent_id = agent_id
        self.user_id = user_id
        self._redis = None
        self._supabase = None

    async def _get_redis(self):
        if self._redis is None:
            try:
                import redis.asyncio as aioredis
                from config.settings import settings
                self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
            except Exception as e:
                logger.warning(f"Redis unavailable: {e} — using in-memory fallback")
                self._redis = InMemoryStore()
        return self._redis

    async def _get_supabase(self):
        if self._supabase is None:
            try:
                from supabase import create_client
                from config.settings import settings
                self._supabase = create_client(settings.supabase_url, settings.supabase_service_key)
            except Exception as e:
                logger.warning(f"Supabase unavailable: {e}")
        return self._supabase

    # ── Short-term Memory (Redis) ──────────────────────────────────────────

    async def remember(self, key: str, value: Any, ttl_seconds: int = 3600):
        """احفظ في الذاكرة القصيرة"""
        redis = await self._get_redis()
        full_key = f"{self.agent_id}:{self.user_id}:{key}"
        try:
            await redis.setex(full_key, ttl_seconds, json.dumps(value, default=str))
        except Exception as e:
            logger.error(f"Memory write error: {e}")

    async def recall(self, key: str) -> Optional[Any]:
        """استرجع من الذاكرة القصيرة"""
        redis = await self._get_redis()
        full_key = f"{self.agent_id}:{self.user_id}:{key}"
        try:
            data = await redis.get(full_key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Memory read error: {e}")
            return None

    async def forget(self, key: str):
        """امسح من الذاكرة القصيرة"""
        redis = await self._get_redis()
        full_key = f"{self.agent_id}:{self.user_id}:{key}"
        await redis.delete(full_key)

    # ── Long-term Memory (Supabase) ────────────────────────────────────────

    async def store_long_term(self, category: str, data: dict):
        """احفظ في الذاكرة الطويلة"""
        supabase = await self._get_supabase()
        if not supabase:
            return

        try:
            supabase.table("agent_memories").insert({
                "agent_id": self.agent_id,
                "user_id": self.user_id,
                "category": category,
                "data": data,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
        except Exception as e:
            logger.error(f"Long-term memory write error: {e}")

    async def retrieve_long_term(self, category: str, limit: int = 10) -> list:
        """استرجع من الذاكرة الطويلة"""
        supabase = await self._get_supabase()
        if not supabase:
            return []

        try:
            result = supabase.table("agent_memories") \
                .select("*") \
                .eq("agent_id", self.agent_id) \
                .eq("user_id", self.user_id) \
                .eq("category", category) \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Long-term memory read error: {e}")
            return []

    # ── Episodic Memory ────────────────────────────────────────────────────

    async def record_success(self, action: str, details: dict, profit: float = 0):
        """سجّل نجاح لتعلّم منه"""
        await self.store_long_term("success", {
            "action": action,
            "details": details,
            "profit": profit,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def record_failure(self, action: str, details: dict, loss: float = 0, reason: str = ""):
        """سجّل إخفاق لتجنّبه"""
        await self.store_long_term("failure", {
            "action": action,
            "details": details,
            "loss": loss,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def get_lessons(self) -> dict:
        """استخرج الدروس من التاريخ"""
        successes = await self.retrieve_long_term("success", limit=20)
        failures = await self.retrieve_long_term("failure", limit=20)
        return {
            "successes": successes,
            "failures": failures,
            "success_count": len(successes),
            "failure_count": len(failures)
        }


class InMemoryStore:
    """Fallback للتطوير بدون Redis"""
    def __init__(self):
        self._store = {}

    async def setex(self, key: str, ttl: int, value: str):
        self._store[key] = value

    async def get(self, key: str) -> Optional[str]:
        return self._store.get(key)

    async def delete(self, key: str):
        self._store.pop(key, None)
