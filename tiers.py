"""
🏛️ TradoAI — Tier Configuration (Python Backend)
Mirror of landing/src/lib/tiers.ts — keep in sync.

مرجع مركزي لكل الباقات والصلاحيات في الـ Backend.
"""
from dataclasses import dataclass, field
from typing import List, Optional


# ─── Tier Slugs ───────────────────────────────────────────────────────────────
TIER_SLUGS = [
    "trial", "micro", "starter", "pro",
    "elite", "whale", "institutional", "founder"
]


@dataclass
class TierConfig:
    slug:             str
    name:             str
    price_monthly:    float
    price_annual:     Optional[float]   # None = annual not available

    # Limits
    signals_per_day:  int               # -1 = unlimited
    exchanges:        int               # -1 = unlimited
    pairs:            int               # -1 = unlimited
    seats:            int               # -1 = unlimited

    # Gates
    features:         List[str] = field(default_factory=list)
    strategies:       List[str] = field(default_factory=list)
    markets:          List[str] = field(default_factory=list)

    # Support
    support_hours:    Optional[float] = None    # None = no support, 0 = 24/7


# ─── Tier Definitions ─────────────────────────────────────────────────────────
TIERS: dict[str, TierConfig] = {

    "trial": TierConfig(
        slug="trial", name="Trial",
        price_monthly=0, price_annual=0,
        signals_per_day=3, exchanges=1, pairs=5, seats=1,
        features=["signals", "alerts"],
        strategies=["trend_following"],
        markets=["spot"],
        support_hours=None,
    ),

    "micro": TierConfig(
        slug="micro", name="Micro",
        price_monthly=29, price_annual=290,
        signals_per_day=5, exchanges=1, pairs=10, seats=1,
        features=["signals", "alerts"],
        strategies=["trend_following", "breakout"],
        markets=["spot"],
        support_hours=None,
    ),

    "starter": TierConfig(
        slug="starter", name="Starter",
        price_monthly=59, price_annual=590,
        signals_per_day=15, exchanges=2, pairs=20, seats=1,
        features=["signals", "alerts", "whale_tracker", "opportunity_hunter"],
        strategies=["trend_following", "breakout", "mean_reversion"],
        markets=["spot", "futures"],
        support_hours=12,
    ),

    "pro": TierConfig(
        slug="pro", name="Pro",
        price_monthly=99, price_annual=990,
        signals_per_day=50, exchanges=3, pairs=50, seats=1,
        features=[
            "signals", "alerts", "whale_tracker", "opportunity_hunter",
            "backtesting", "strategy_builder", "portfolio_manager",
        ],
        strategies=["trend_following", "breakout", "mean_reversion", "scalping", "custom"],
        markets=["spot", "futures", "perpetuals"],
        support_hours=1,
    ),

    "elite": TierConfig(
        slug="elite", name="Elite",
        price_monthly=199, price_annual=1990,
        signals_per_day=150, exchanges=5, pairs=-1, seats=1,
        features=[
            "signals", "alerts", "whale_tracker", "opportunity_hunter",
            "auto_execute", "backtesting", "strategy_builder",
            "portfolio_manager", "multi_portfolio", "custom_risk_limits",
            "api_access", "tax_reporting",
        ],
        strategies=["trend_following", "breakout", "mean_reversion", "scalping", "custom", "multi_strategy"],
        markets=["spot", "futures", "perpetuals", "options"],
        support_hours=0.25,
    ),

    "whale": TierConfig(
        slug="whale", name="Whale",
        price_monthly=499, price_annual=4990,
        signals_per_day=-1, exchanges=10, pairs=-1, seats=1,
        features=[
            "signals", "alerts", "whale_tracker", "opportunity_hunter",
            "auto_execute", "backtesting", "strategy_builder",
            "portfolio_manager", "multi_portfolio", "custom_risk_limits",
            "api_access", "tax_reporting", "early_signals",
            "dedicated_manager", "strategy_calls", "daily_reports",
        ],
        strategies=["trend_following", "breakout", "mean_reversion", "scalping", "custom", "multi_strategy", "institutional"],
        markets=["spot", "futures", "perpetuals", "options", "defi"],
        support_hours=0,
    ),

    "institutional": TierConfig(
        slug="institutional", name="Institutional",
        price_monthly=1499, price_annual=14990,
        signals_per_day=-1, exchanges=-1, pairs=-1, seats=-1,
        features=[
            "signals", "alerts", "whale_tracker", "opportunity_hunter",
            "auto_execute", "backtesting", "strategy_builder",
            "portfolio_manager", "multi_portfolio", "custom_risk_limits",
            "api_access", "tax_reporting", "early_signals",
            "dedicated_manager", "strategy_calls", "daily_reports",
            "white_label", "sub_accounts", "compliance_reports", "sla_99_9",
        ],
        strategies=["trend_following", "breakout", "mean_reversion", "scalping", "custom", "multi_strategy", "institutional"],
        markets=["spot", "futures", "perpetuals", "options", "defi", "cfd"],
        support_hours=0,
    ),

    "founder": TierConfig(
        slug="founder", name="Founder",
        price_monthly=2999, price_annual=None,
        signals_per_day=-1, exchanges=-1, pairs=-1, seats=100,
        features=[
            "signals", "alerts", "whale_tracker", "opportunity_hunter",
            "auto_execute", "backtesting", "strategy_builder",
            "portfolio_manager", "multi_portfolio", "custom_risk_limits",
            "api_access", "tax_reporting", "early_signals",
            "dedicated_manager", "strategy_calls", "daily_reports",
            "white_label", "sub_accounts", "compliance_reports", "sla_99_9",
            "founder_badge", "roadmap_voting",
        ],
        strategies=["trend_following", "breakout", "mean_reversion", "scalping", "custom", "multi_strategy", "institutional"],
        markets=["spot", "futures", "perpetuals", "options", "defi", "cfd"],
        support_hours=0,
    ),
}


# ─── Helper Functions ─────────────────────────────────────────────────────────

def get_tier(slug: str) -> TierConfig:
    """جلب إعدادات الباقة (يرجع trial في حال عدم الوجود)"""
    return TIERS.get(slug, TIERS["trial"])


def has_feature(tier_slug: str, feature: str) -> bool:
    """هل لدى المستخدم ميزة معينة؟"""
    return feature in get_tier(tier_slug).features


def can_add_exchange(tier_slug: str, current_count: int) -> bool:
    """هل يمكن إضافة منصة أخرى؟"""
    limit = get_tier(tier_slug).exchanges
    return limit == -1 or current_count < limit


def can_add_pair(tier_slug: str, current_count: int) -> bool:
    """هل يمكن إضافة زوج آخر؟"""
    limit = get_tier(tier_slug).pairs
    return limit == -1 or current_count < limit


def signals_remaining(tier_slug: str, used_today: int) -> int:
    """الإشارات المتبقية اليوم (-1 = unlimited)"""
    limit = get_tier(tier_slug).signals_per_day
    if limit == -1:
        return -1
    return max(0, limit - used_today)


def can_auto_execute(tier_slug: str) -> bool:
    """هل الباقة تدعم التنفيذ التلقائي؟ (Elite وما فوق)"""
    return has_feature(tier_slug, "auto_execute")


def check_signal_limit(tier_slug: str, used_today: int):
    """يرفع استثناء إذا تجاوز المستخدم حد الإشارات"""
    from fastapi import HTTPException
    remaining = signals_remaining(tier_slug, used_today)
    if remaining == 0:
        tier = get_tier(tier_slug)
        raise HTTPException(
            status_code=429,
            detail=f"Daily signal limit reached ({tier.signals_per_day}/day). Upgrade for more."
        )


# ─── Tier Comparison (for upgrade prompts) ────────────────────────────────────

TIER_ORDER = ["trial", "micro", "starter", "pro", "elite", "whale", "institutional", "founder"]


def is_higher_tier(a: str, b: str) -> bool:
    """هل الباقة a أعلى من b؟"""
    idx_a = TIER_ORDER.index(a) if a in TIER_ORDER else 0
    idx_b = TIER_ORDER.index(b) if b in TIER_ORDER else 0
    return idx_a > idx_b


def upgrade_suggestions(tier_slug: str, requested_feature: str) -> Optional[str]:
    """أدنى باقة تدعم الميزة المطلوبة"""
    for slug in TIER_ORDER:
        if slug == tier_slug:
            continue
        if is_higher_tier(slug, tier_slug) and has_feature(slug, requested_feature):
            return slug
    return None
