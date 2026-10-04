"""القيم المعتمدة من المالك (أكتوبر 2026). ثابتة؛ لا تُقرأ من env حتى لا تُغيَّر بالخطأ."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Limits:
    # المال (نسب من رصيد الحساب) — تسري على paper وlive سواء
    max_risk_per_trade_pct: float = 1.0
    max_daily_loss_pct: float = 3.0        # بلوغه = إيقاف التنفيذ لهذا اليوم
    max_monthly_drawdown_pct: float = 8.0  # بلوغه = إيقاف الاستراتيجية وتخفيض درجتها
    max_concurrent_positions: int = 3
    max_correlated_positions: int = 2      # مراكز في نفس اتجاه BTC

    # الإنفاق (USD/شهر) — معتمدة: 100 و 25
    ai_monthly_usd: float = 100.0
    ai_warn_ratio: float = 0.8             # تحذير عند 80 دولار
    fly_monthly_usd: float = 25.0

    # التطوير الذاتي
    max_self_pr_lines: int = 300
    protected_paths: tuple = ("governance/", "auth/", "payments/", ".github/", "config/models.py")

    # الصلاحيات
    level2_expiry_hours: int = 48
    promotion_clean_days: int = 30
    paper_min_days: int = 60
    paper_min_closed_trades: int = 80


LIMITS = Limits()
