"""
AIBudget — سقف إنفاق الـ AI الشهري (100 دولار) وتنزيل الفئات.

المصدر: مجموع llm_call في nervous_metrics للشهر الجاري.
يُحقن في LLMRouter كـ budget_check. بلا قاعدة بيانات = لا تجاوز (ويُسجَّل تحذير مرة).
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Callable, Optional

from loguru import logger

from governance.limits import LIMITS


class AIBudget:
    def __init__(self, spent_reader: Optional[Callable[[], float]] = None, cache_ttl_s: int = 300):
        self._reader = spent_reader or self._default_reader
        self._ttl = cache_ttl_s
        self._cached: tuple[float, float] = (0.0, 0.0)  # (value, ts)
        self._warned = False

    def spent_this_month(self) -> float:
        if time.time() - self._cached[1] < self._ttl:
            return self._cached[0]
        try:
            v = float(self._reader())
        except Exception as ex:  # noqa: BLE001
            if not self._warned:
                logger.warning(f"AIBudget: تعذر قراءة الإنفاق ({ex}) — أعتبره 0")
                self._warned = True
            v = 0.0
        self._cached = (v, time.time())
        return v

    def status(self) -> dict:
        s = self.spent_this_month()
        cap = LIMITS.ai_monthly_usd
        return {"spent_usd": round(s, 2), "cap_usd": cap, "ratio": round(s / cap, 3) if cap else 0,
                "warn": s >= cap * LIMITS.ai_warn_ratio, "exceeded": s >= cap}

    def exceeded(self, agent_id: str = "") -> bool:
        return self.status()["exceeded"]

    @staticmethod
    def _default_reader() -> float:
        if os.getenv("NERVOUS_METRICS_ENABLED", "").lower() not in ("1", "true"):
            return 0.0
        from db.client import get_supabase
        start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
        rows = (get_supabase(service_role=True).table("nervous_metrics").select("value")
                .eq("name", "llm_call").gte("ts", start).execute().data or [])
        return sum(float(r["value"]) for r in rows)
