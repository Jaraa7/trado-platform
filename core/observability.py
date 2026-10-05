"""
core/observability.py — تهيئة Sentry مرة واحدة للـ API والدماغ.

- بلا SENTRY_DSN = لا شيء يحدث (الاختبارات والتشغيل المحلي لا تتأثر).
- لا تُرسل بيانات شخصية (send_default_pii=False).
- brain_checkin(): نبضة Sentry Cron بعد كل دورة للدماغ؛ إن تأخرت يصل تنبيه.
"""
from __future__ import annotations

import os

_ready = False


def init_sentry(component: str) -> bool:
    global _ready
    dsn = os.getenv("SENTRY_DSN", "")
    if not dsn or _ready:
        return _ready
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=dsn,
            environment=os.getenv("APP_ENV", "development"),
            release=os.getenv("FLY_IMAGE_REF", "local"),
            server_name=f"trado-{component}",
            traces_sample_rate=0.05,     # 5% فقط ضمن الخطة المجانية
            send_default_pii=False,
        )
        sentry_sdk.set_tag("component", component)
        _ready = True
    except Exception:  # noqa: BLE001 — المراقبة لا تُسقط التطبيق أبدًا
        _ready = False
    return _ready


def brain_checkin(status: str = "ok") -> None:
    """status: 'in_progress' | 'ok' | 'error'. جدول الدماغ: كل ساعة، سماح 20 دقيقة."""
    if not _ready:
        return
    try:
        from sentry_sdk.crons import capture_checkin
        capture_checkin(
            monitor_slug="trado-brain-tick",
            status=status,
            monitor_config={
                "schedule": {"type": "interval", "value": 1, "unit": "hour"},
                "checkin_margin": 20,
                "max_runtime": 10,
                "timezone": "UTC",
            },
        )
    except Exception:  # noqa: BLE001
        pass
