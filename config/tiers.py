"""
TRADO Tier System v2.0
8 باقات مع unit economics سليمة
"""
from dataclasses import dataclass, field
from enum import Enum


class TierName(str, Enum):
    TRIAL          = "trial"
    MICRO          = "micro"
    STARTER        = "starter"
    PRO            = "pro"
    ELITE          = "elite"
    WHALE          = "whale"
    INSTITUTIONAL  = "institutional"
    FOUNDER        = "founder"
    ENTERPRISE     = "enterprise"


@dataclass
class TierFeatures:
    # Signals
    signals_per_day: int
    exchanges_count: int
    backtesting: str           # "none" | "limited" | "unlimited"
    custom_strategies: bool

    # Agents access
    all_87_agents: bool        # always True (الميزات محفوظة)
    whale_tracker_live: bool
    arbitrage_alerts: bool
    pattern_recognition: bool
    macro_reports: bool
    portfolio_manager: bool

    # Support
    support_level: str         # "email" | "chat" | "live" | "phone" | "dedicated"
    response_time_hours: float

    # Premium
    tax_reporting: bool
    custom_alerts_unlimited: bool
    multi_account: int         # 1 | 5 | 25 | unlimited
    api_access: bool
    one_on_one_calls: int      # per month

    # Enterprise
    white_label: bool
    custom_branding: bool
    dedicated_infra: bool
    sla_uptime: float          # 0.99 | 0.995 | 0.999 | 0.9999


@dataclass
class Tier:
    name: TierName
    display_name: str
    emoji: str
    target_portfolio: str
    price_monthly: float
    price_annually: float
    cost_per_user: float
    features: TierFeatures

    @property
    def margin_monthly(self) -> float:
        if self.price_monthly == 0:
            return 0
        return (self.price_monthly - self.cost_per_user) / self.price_monthly

    @property
    def margin_pct(self) -> str:
        return f"{self.margin_monthly * 100:.0f}%"

    @property
    def annual_discount_pct(self) -> int:
        if self.price_monthly == 0:
            return 0
        full_yearly = self.price_monthly * 12
        return int((1 - self.price_annually / full_yearly) * 100)


# ═══════════════════════════════════════════════════════════════
# تعريف الـ 8 باقات
# ═══════════════════════════════════════════════════════════════

TIERS: dict[TierName, Tier] = {
    TierName.TRIAL: Tier(
        name=TierName.TRIAL,
        display_name="Trial",
        emoji="🌱",
        target_portfolio="استكشاف",
        price_monthly=0,
        price_annually=0,
        cost_per_user=8,
        features=TierFeatures(
            signals_per_day=10, exchanges_count=1, backtesting="limited",
            custom_strategies=False, all_87_agents=True,
            whale_tracker_live=False, arbitrage_alerts=False,
            pattern_recognition=True, macro_reports=False, portfolio_manager=False,
            support_level="email", response_time_hours=48,
            tax_reporting=False, custom_alerts_unlimited=False,
            multi_account=1, api_access=False, one_on_one_calls=0,
            white_label=False, custom_branding=False,
            dedicated_infra=False, sla_uptime=0.99
        )
    ),

    TierName.MICRO: Tier(
        name=TierName.MICRO,
        display_name="Micro",
        emoji="🌱",
        target_portfolio="$500 - $5,000",
        price_monthly=29,
        price_annually=290,    # 17% off
        cost_per_user=12,
        features=TierFeatures(
            signals_per_day=5, exchanges_count=1, backtesting="none",
            custom_strategies=False, all_87_agents=True,
            whale_tracker_live=False, arbitrage_alerts=False,
            pattern_recognition=True, macro_reports=True, portfolio_manager=False,
            support_level="email", response_time_hours=24,
            tax_reporting=False, custom_alerts_unlimited=False,
            multi_account=1, api_access=False, one_on_one_calls=0,
            white_label=False, custom_branding=False,
            dedicated_infra=False, sla_uptime=0.99
        )
    ),

    TierName.STARTER: Tier(
        name=TierName.STARTER,
        display_name="Starter",
        emoji="🚀",
        target_portfolio="$2,000 - $20,000",
        price_monthly=59,
        price_annually=590,
        cost_per_user=25,
        features=TierFeatures(
            signals_per_day=15, exchanges_count=2, backtesting="limited",
            custom_strategies=False, all_87_agents=True,
            whale_tracker_live=True, arbitrage_alerts=False,
            pattern_recognition=True, macro_reports=True, portfolio_manager=False,
            support_level="chat", response_time_hours=12,
            tax_reporting=False, custom_alerts_unlimited=False,
            multi_account=1, api_access=False, one_on_one_calls=0,
            white_label=False, custom_branding=False,
            dedicated_infra=False, sla_uptime=0.99
        )
    ),

    TierName.PRO: Tier(
        name=TierName.PRO,
        display_name="Pro",
        emoji="💎",
        target_portfolio="$10,000 - $100,000",
        price_monthly=99,
        price_annually=990,
        cost_per_user=45,
        features=TierFeatures(
            signals_per_day=50, exchanges_count=3, backtesting="unlimited",
            custom_strategies=True, all_87_agents=True,
            whale_tracker_live=True, arbitrage_alerts=True,
            pattern_recognition=True, macro_reports=True, portfolio_manager=True,
            support_level="live", response_time_hours=1,
            tax_reporting=False, custom_alerts_unlimited=True,
            multi_account=1, api_access=False, one_on_one_calls=0,
            white_label=False, custom_branding=False,
            dedicated_infra=False, sla_uptime=0.995
        )
    ),

    TierName.ELITE: Tier(
        name=TierName.ELITE,
        display_name="Elite",
        emoji="👑",
        target_portfolio="$50,000 - $500,000",
        price_monthly=199,
        price_annually=1990,
        cost_per_user=75,
        features=TierFeatures(
            signals_per_day=9999,    # unlimited
            exchanges_count=5,
            backtesting="unlimited",
            custom_strategies=True, all_87_agents=True,
            whale_tracker_live=True, arbitrage_alerts=True,
            pattern_recognition=True, macro_reports=True, portfolio_manager=True,
            support_level="phone", response_time_hours=0.25,  # 15 min
            tax_reporting=True, custom_alerts_unlimited=True,
            multi_account=3, api_access=True, one_on_one_calls=1,
            white_label=False, custom_branding=False,
            dedicated_infra=False, sla_uptime=0.999
        )
    ),

    TierName.WHALE: Tier(
        name=TierName.WHALE,
        display_name="Whale",
        emoji="🐋",
        target_portfolio="$200,000 - $5M",
        price_monthly=499,
        price_annually=4990,
        cost_per_user=120,
        features=TierFeatures(
            signals_per_day=9999, exchanges_count=9999, backtesting="unlimited",
            custom_strategies=True, all_87_agents=True,
            whale_tracker_live=True, arbitrage_alerts=True,
            pattern_recognition=True, macro_reports=True, portfolio_manager=True,
            support_level="dedicated", response_time_hours=0.1,
            tax_reporting=True, custom_alerts_unlimited=True,
            multi_account=5, api_access=True, one_on_one_calls=4,
            white_label=False, custom_branding=False,
            dedicated_infra=False, sla_uptime=0.999
        )
    ),

    TierName.INSTITUTIONAL: Tier(
        name=TierName.INSTITUTIONAL,
        display_name="Institutional",
        emoji="🏛️",
        target_portfolio="صناديق + Family Offices",
        price_monthly=1499,
        price_annually=14990,
        cost_per_user=250,
        features=TierFeatures(
            signals_per_day=9999, exchanges_count=9999, backtesting="unlimited",
            custom_strategies=True, all_87_agents=True,
            whale_tracker_live=True, arbitrage_alerts=True,
            pattern_recognition=True, macro_reports=True, portfolio_manager=True,
            support_level="dedicated", response_time_hours=0.05,
            tax_reporting=True, custom_alerts_unlimited=True,
            multi_account=25, api_access=True, one_on_one_calls=8,
            white_label=True, custom_branding=True,
            dedicated_infra=True, sla_uptime=0.9999
        )
    ),

    TierName.FOUNDER: Tier(
        name=TierName.FOUNDER,
        display_name="Founder's Circle",
        emoji="🌟",
        target_portfolio="حصري — 100 شخص فقط",
        price_monthly=2999,
        price_annually=29990,
        cost_per_user=350,    # خدمات إضافية
        features=TierFeatures(
            signals_per_day=9999, exchanges_count=9999, backtesting="unlimited",
            custom_strategies=True, all_87_agents=True,
            whale_tracker_live=True, arbitrage_alerts=True,
            pattern_recognition=True, macro_reports=True, portfolio_manager=True,
            support_level="dedicated", response_time_hours=0.01,
            tax_reporting=True, custom_alerts_unlimited=True,
            multi_account=999, api_access=True, one_on_one_calls=999,
            white_label=True, custom_branding=True,
            dedicated_infra=True, sla_uptime=0.9999
        )
    ),

    TierName.ENTERPRISE: Tier(
        name=TierName.ENTERPRISE,
        display_name="Enterprise",
        emoji="🏢",
        target_portfolio="بنوك + صناديق سيادية",
        price_monthly=5000,    # starting price
        price_annually=50000,
        cost_per_user=500,
        features=TierFeatures(
            signals_per_day=9999, exchanges_count=9999, backtesting="unlimited",
            custom_strategies=True, all_87_agents=True,
            whale_tracker_live=True, arbitrage_alerts=True,
            pattern_recognition=True, macro_reports=True, portfolio_manager=True,
            support_level="dedicated", response_time_hours=0.01,
            tax_reporting=True, custom_alerts_unlimited=True,
            multi_account=9999, api_access=True, one_on_one_calls=9999,
            white_label=True, custom_branding=True,
            dedicated_infra=True, sla_uptime=0.9999
        )
    ),
}


# ═══════════════════════════════════════════════════════════════
# Add-ons (إضافات اختيارية)
# ═══════════════════════════════════════════════════════════════

@dataclass
class AddOn:
    id: str
    name: str
    price: float
    description: str
    available_for: list[TierName]


ADD_ONS = {
    "training_hour": AddOn(
        id="training_hour",
        name="🎓 1-on-1 Training (ساعة)",
        price=99,
        description="جلسة تدريب فردية مع خبير تداول",
        available_for=[TierName.PRO, TierName.ELITE, TierName.WHALE]
    ),
    "strategy_call": AddOn(
        id="strategy_call",
        name="📞 Strategy Call (30 دقيقة)",
        price=49,
        description="استشارة استراتيجية مع خبير",
        available_for=[TierName.MICRO, TierName.STARTER, TierName.PRO]
    ),
    "custom_strategy": AddOn(
        id="custom_strategy",
        name="📈 Custom Strategy Build",
        price=499,
        description="بناء استراتيجية مخصصة لاحتياجاتك",
        available_for=[TierName.PRO, TierName.ELITE]
    ),
    "custom_bot": AddOn(
        id="custom_bot",
        name="🤖 Custom Bot Development",
        price=1999,
        description="بوت مخصص بمنطقك",
        available_for=[TierName.WHALE, TierName.INSTITUTIONAL]
    ),
    "audit_report": AddOn(
        id="audit_report",
        name="📋 Monthly Audit Report",
        price=199,
        description="تقرير شهري لمراجعة الأداء",
        available_for=[TierName.ELITE, TierName.WHALE, TierName.INSTITUTIONAL]
    ),
}


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def get_tier(tier_name: TierName | str) -> Tier:
    if isinstance(tier_name, str):
        tier_name = TierName(tier_name)
    return TIERS[tier_name]


def calculate_total_mrr(tier_distribution: dict[TierName, int]) -> dict:
    """حساب MRR من توزيع الـ users على الباقات"""
    total_revenue = 0
    total_cost = 0
    total_users = 0

    breakdown = []
    for tier_name, user_count in tier_distribution.items():
        tier = TIERS[tier_name]
        revenue = tier.price_monthly * user_count
        cost = tier.cost_per_user * user_count
        total_revenue += revenue
        total_cost += cost
        total_users += user_count
        breakdown.append({
            "tier": tier.display_name,
            "users": user_count,
            "revenue": revenue,
            "cost": cost,
            "margin": revenue - cost
        })

    return {
        "total_users": total_users,
        "mrr": total_revenue,
        "monthly_cost": total_cost,
        "profit": total_revenue - total_cost,
        "margin_pct": (total_revenue - total_cost) / total_revenue if total_revenue > 0 else 0,
        "arr": total_revenue * 12,
        "breakdown": breakdown
    }


def get_upgrade_path(current_tier: TierName) -> TierName | None:
    """الباقة التالية المقترحة للترقية"""
    progression = [
        TierName.TRIAL, TierName.MICRO, TierName.STARTER, TierName.PRO,
        TierName.ELITE, TierName.WHALE, TierName.INSTITUTIONAL, TierName.FOUNDER
    ]
    try:
        idx = progression.index(current_tier)
        if idx < len(progression) - 1:
            return progression[idx + 1]
    except ValueError:
        pass
    return None


def print_pricing_table():
    """عرض جدول الأسعار"""
    print("\n" + "═" * 75)
    print(f"{'الباقة':<20} {'الشهري':>10} {'السنوي':>10} {'التكلفة':>10} {'الهامش':>8}")
    print("═" * 75)
    for tier in TIERS.values():
        if tier.name == TierName.TRIAL:
            print(f"{tier.emoji} {tier.display_name:<17} {'مجاناً':>10} {'مجاناً':>10} {f'${tier.cost_per_user}':>10} {'N/A':>8}")
        elif tier.name == TierName.ENTERPRISE:
            print(f"{tier.emoji} {tier.display_name:<17} {'Custom':>10} {'Custom':>10} {f'${tier.cost_per_user}+':>10} {'High':>8}")
        else:
            print(
                f"{tier.emoji} {tier.display_name:<17} "
                f"${tier.price_monthly:>8} "
                f"${tier.price_annually:>9} "
                f"${tier.cost_per_user:>9} "
                f"{tier.margin_pct:>8}"
            )
    print("═" * 75)


if __name__ == "__main__":
    print_pricing_table()

    # محاكاة الهدف السنوي
    print("\n📊 توقع السنة الأولى:")
    print("─" * 50)
    target = {
        TierName.MICRO: 500,
        TierName.STARTER: 300,
        TierName.PRO: 250,
        TierName.ELITE: 100,
        TierName.WHALE: 30,
        TierName.INSTITUTIONAL: 10,
        TierName.FOUNDER: 5,
        TierName.ENTERPRISE: 2,
    }
    result = calculate_total_mrr(target)
    print(f"  المستخدمون:    {result['total_users']:,}")
    print(f"  MRR:           ${result['mrr']:,.0f}")
    print(f"  Monthly Cost:  ${result['monthly_cost']:,.0f}")
    print(f"  💰 Profit/mo:  ${result['profit']:,.0f}")
    print(f"  📊 Margin:     {result['margin_pct']*100:.1f}%")
    print(f"  🎯 ARR:        ${result['arr']:,.0f}")
