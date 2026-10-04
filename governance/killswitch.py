"""
KillSwitch — إيقاف كل تنفيذ ونشر خلال ثوانٍ.

يُقرأ من Redis مباشرة في طبقة التنفيذ (لا عبر الدماغ) حتى يعمل ولو تعطل الدماغ.
بلا Redis يسقط إلى ملف محلي (يكفي لعملية واحدة، ويُسجَّل تحذير).
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional

from loguru import logger

KEY = "nervous:killswitch"
_FALLBACK = Path(os.getenv("NERVOUS_KILLSWITCH_FILE", "data/nervous_killswitch.json"))


class KillSwitch:
    def __init__(self, redis_client=None):
        self._r = redis_client
        if self._r is None:
            url = os.getenv("REDIS_URL", "")
            if url:
                try:
                    import redis
                    self._r = redis.from_url(url, decode_responses=True)
                    self._r.ping()
                except Exception as ex:  # noqa: BLE001
                    logger.warning(f"KillSwitch: Redis غير متاح ({ex}) — fallback إلى ملف")
                    self._r = None

    # ── القراءة (سريعة، تُستدعى قبل كل أمر تنفيذ) ─────────────────
    def state(self) -> dict:
        raw: Optional[str] = None
        if self._r is not None:
            try:
                raw = self._r.get(KEY)
            except Exception as ex:  # noqa: BLE001
                logger.error(f"KillSwitch: فشل قراءة Redis ({ex}) — أعتبر النظام موقوفًا احتياطًا")
                return {"stopped": True, "reason": "redis_unreachable", "by": "system", "ts": time.time()}
        elif _FALLBACK.exists():
            raw = _FALLBACK.read_text(encoding="utf-8")
        return json.loads(raw) if raw else {"stopped": False}

    def is_stopped(self) -> bool:
        return bool(self.state().get("stopped"))

    # ── الكتابة ──────────────────────────────────────────────────────
    def _write(self, st: dict):
        raw = json.dumps(st, ensure_ascii=False)
        if self._r is not None:
            self._r.set(KEY, raw)
        else:
            _FALLBACK.parent.mkdir(parents=True, exist_ok=True)
            _FALLBACK.write_text(raw, encoding="utf-8")

    def stop(self, reason: str, by: str) -> dict:
        st = {"stopped": True, "reason": reason, "by": by, "ts": time.time()}
        self._write(st)
        logger.critical(f"🛑 KILL SWITCH ON — {reason} (by {by})")
        return st

    def resume(self, by: str) -> dict:
        st = {"stopped": False, "resumed_by": by, "ts": time.time()}
        self._write(st)
        logger.warning(f"▶️ KILL SWITCH OFF (by {by})")
        return st


def assert_not_stopped(ks: Optional[KillSwitch] = None):
    """تُستدعى في أول سطر من أي دالة تنفّذ أمرًا أو نشرًا."""
    ks = ks or KillSwitch()
    st = ks.state()
    if st.get("stopped"):
        raise RuntimeError(f"النظام موقوف (kill switch): {st.get('reason')}")
