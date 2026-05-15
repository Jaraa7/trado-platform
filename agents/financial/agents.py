"""
🟫 Financial Department — 12 Agents
قسم المالية: استدامة المشروع بهامش 40%+
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from agents._shared.agent_factory import create_agent_class
from agents._shared.base_agent import BaseAgent, AgentContext, AgentResponse


# ═════════════════════════════════════════════════════════════════════
# 4.1 Pricing Strategist 💎
# ═════════════════════════════════════════════════════════════════════

PricingStrategist = create_agent_class(
    agent_id="pricing_strategist",
    agent_name="Pricing Strategist 💎",
    role_description="""أنت Pricing Strategist، خبيرة 25 سنة في تسعير SaaS.
عملت مع Salesforce, HubSpot, Shopify. تعرف Value-Based vs Cost-Plus vs Competitive Pricing.
تدرس السوق + المنافسين + القدرة الشرائية لكل شريحة.""",
    expertise="25 سنة | SaaS pricing for Salesforce/HubSpot/Shopify",
    output_format="""```
💎 PRICING RECOMMENDATION
━━━━━━━━━━━━━━━━━━━━━━━
🎯 الباقة المقترحة: [name]
💰 السعر: $[X]/شهر
📊 Margin متوقع: [X]%
🌍 PPP adjustment: [قائمة بلدان]
✅ المنطق: [3 جمل]
```""",
    skills=[
        "Competitive pricing analysis",
        "Value-based pricing",
        "Cost-plus pricing",
        "Penetration pricing",
        "Premium pricing",
        "PPP (geographic pricing)",
        "Bundle pricing",
        "Tiered pricing",
        "Freemium model design",
        "Free trial optimization",
        "Promotional pricing",
        "Discount strategy",
        "Price anchoring",
        "Decoy pricing",
        "Psychological pricing",
        "B2B pricing",
        "Enterprise pricing",
        "PAYG vs subscription",
        "Price A/B testing",
        "Price elasticity"
    ]
)


# ═════════════════════════════════════════════════════════════════════
# 4.2 Cost Tracker 📉
# ═════════════════════════════════════════════════════════════════════

@dataclass
class CostBreakdown:
    ai_apis: float = 0
    infrastructure: float = 0
    third_party: float = 0
    payment_fees: float = 0
    other: float = 0

    @property
    def total(self) -> float:
        return sum([self.ai_apis, self.infrastructure, self.third_party, self.payment_fees, self.other])


class CostTracker(BaseAgent):
    AGENT_ID = "cost_tracker"
    AGENT_NAME = "Cost Tracker 📉"
    MODEL = "claude-haiku-4-5"
    MAX_TOKENS = 1500

    def __init__(self, user_id: str = "system"):
        super().__init__(user_id)
        self._daily_costs = []
        self._cost_alerts = []

    @property
    def system_prompt(self) -> str:
        return """أنت Cost Tracker، تراقب كل دولار بدقة.
تعرف بالضبط: per-user cost, per-agent cost, per-feature cost.
تنبه قبل أن نخسر."""

    def record_cost(self, category: str, amount: float, user_id: str = "system"):
        self._daily_costs.append({
            "category": category,
            "amount": amount,
            "user": user_id,
            "timestamp": datetime.utcnow().isoformat()
        })

    def daily_summary(self) -> CostBreakdown:
        breakdown = CostBreakdown()
        today = datetime.utcnow().date()

        for cost in self._daily_costs:
            try:
                cost_date = datetime.fromisoformat(cost["timestamp"]).date()
                if cost_date == today:
                    cat = cost["category"]
                    amount = cost["amount"]
                    if cat == "ai_api":
                        breakdown.ai_apis += amount
                    elif cat == "infrastructure":
                        breakdown.infrastructure += amount
                    elif cat == "third_party":
                        breakdown.third_party += amount
                    elif cat == "payment":
                        breakdown.payment_fees += amount
                    else:
                        breakdown.other += amount
            except Exception:
                continue

        return breakdown


# ═════════════════════════════════════════════════════════════════════
# 4.3 Revenue Optimizer 💵
# ═════════════════════════════════════════════════════════════════════

RevenueOptimizer = create_agent_class(
    agent_id="revenue_optimizer",
    agent_name="Revenue Optimizer 💵",
    role_description="""أنت Revenue Optimizer، تعظّم الإيرادات من كل مستخدم (ARPU).
تكتشف فرص upsell و cross-sell، وتصمم حملات win-back.""",
    expertise="18 سنة | زادت ARPU لـ 50+ شركة بنسبة 30-150%",
    output_format="""```
💵 REVENUE OPTIMIZATION
━━━━━━━━━━━━━━━━━━━━━
📊 ARPU الحالي: $[X]
🎯 ARPU المستهدف: $[X] (+[X]%)
💡 فرص:
  1. [upsell opportunity]
  2. [cross-sell opportunity]
📅 خطة 30 يوم: [steps]
```""",
    skills=[
        "ARPU analysis", "Upsell identification", "Cross-sell suggestions",
        "Personalized upgrade prompts", "Behavioral analysis", "Win-back campaigns",
        "Loyalty program design", "Add-on services", "Premium features marketing",
        "Bundle creation", "Annual conversion", "Volume discounts",
        "Referral incentives", "Extension promos", "Reactivation",
        "Trial-to-paid", "Free-to-paid", "Churn prevention offers",
        "Cohort analysis", "Revenue forecasting"
    ]
)


# ═════════════════════════════════════════════════════════════════════
# 4.4 Subscription Manager 📅
# ═════════════════════════════════════════════════════════════════════

@dataclass
class Subscription:
    user_id: str
    tier: str
    status: str  # active/grace/cancelled/expired
    started_at: str
    renewal_at: str
    amount: float
    currency: str = "USD"
    auto_renew: bool = True


class SubscriptionManager(BaseAgent):
    AGENT_ID = "subscription_manager"
    AGENT_NAME = "Subscription Manager 📅"
    MODEL = "claude-haiku-4-5"
    MAX_TOKENS = 1200

    @property
    def system_prompt(self) -> str:
        return """أنت Subscription Manager، تدير الاشتراكات بسلاسة.
تتعامل مع: تجديد، إلغاء، ترقية، تخفيض، grace periods، failed payments."""

    def days_until_renewal(self, sub: Subscription) -> int:
        renewal = datetime.fromisoformat(sub.renewal_at)
        return (renewal - datetime.utcnow()).days

    def should_notify(self, sub: Subscription) -> str:
        days = self.days_until_renewal(sub)
        if days == 7:
            return "7_day_reminder"
        elif days == 3:
            return "3_day_reminder"
        elif days == 1:
            return "tomorrow_renewal"
        elif days == 0:
            return "today_renewal"
        elif days < 0 and abs(days) <= 3:
            return "grace_period"
        return ""


# ═════════════════════════════════════════════════════════════════════
# 4.5 Payment Gateway Manager 💳
# ═════════════════════════════════════════════════════════════════════

class PaymentGatewayManager(BaseAgent):
    AGENT_ID = "payment_gateway"
    AGENT_NAME = "Payment Gateway Manager 💳"
    MODEL = "claude-haiku-4-5"
    MAX_TOKENS = 1000

    GATEWAY_ROUTING = {
        "KW": ["knet", "lemon_squeezy"],
        "SA": ["mada", "lemon_squeezy"],
        "AE": ["lemon_squeezy"],
        "EU": ["lemon_squeezy"],
        "US": ["stripe", "lemon_squeezy"],
        "default": ["lemon_squeezy", "crypto"]
    }

    @property
    def system_prompt(self) -> str:
        return """أنت Payment Gateway Manager.
تختار البوابة الأنسب لكل بلد + تتعامل مع الفشل + توجّه الحلول البديلة."""

    def select_gateway(self, country: str) -> list[str]:
        return self.GATEWAY_ROUTING.get(country.upper(), self.GATEWAY_ROUTING["default"])

    def estimate_fee(self, amount: float, gateway: str) -> float:
        fees = {
            "lemon_squeezy": 0.05 * amount + 0.30,  # 5% + $0.30
            "stripe": 0.029 * amount + 0.30,         # 2.9% + $0.30
            "knet": 0.015 * amount,                  # 1.5%
            "mada": 0.02 * amount,                   # 2%
            "crypto": 0.005 * amount,                # 0.5% network
        }
        return fees.get(gateway, 0.05 * amount)


# ═════════════════════════════════════════════════════════════════════
# 4.6 Failed Payment Recovery 🚨
# ═════════════════════════════════════════════════════════════════════

FailedPaymentRecovery = create_agent_class(
    agent_id="failed_payment_recovery",
    agent_name="Failed Payment Recovery 🚨",
    role_description="""أنت Failed Payment Recovery، تنقذ الاشتراكات الفاشلة.
معدل استرداد متوقع: 40-60% من المدفوعات الفاشلة.""",
    expertise="10 سنة | dunning management | استرداد ملايين الدولارات",
    output_format="""```
🚨 RECOVERY STRATEGY
━━━━━━━━━━━━━━━━━━━━
📊 سبب الفشل: [reason]
⏱️  Retry timeline: [1d, 3d, 5d, 7d]
💌 Email sequence: [Arabic + English]
💰 Discount offer: [10%/20%/30%]
📈 احتمال الاسترداد: [X]%
```""",
    skills=[
        "Smart retry timing", "Soft decline handling", "Hard decline strategies",
        "Card update prompts", "Friendly reminder emails", "Personalized win-back",
        "Discount calibration", "Telegram dunning", "SMS reminders",
        "Multi-channel approach", "Grace period extension", "Pause vs Cancel",
        "Cancellation surveys", "Exit interviews", "Re-activation campaigns",
        "Win-back analytics", "Recovery rate tracking", "Cost per recovery",
        "LTV impact", "Churn reduction"
    ]
)


# ═════════════════════════════════════════════════════════════════════
# 4.7 Financial Forecaster 🔮
# ═════════════════════════════════════════════════════════════════════

@dataclass
class FinancialMetrics:
    mrr: float = 0
    arr: float = 0
    churn_rate: float = 0
    ltv: float = 0
    cac: float = 0

    @property
    def ltv_cac_ratio(self) -> float:
        return self.ltv / self.cac if self.cac > 0 else 0

    @property
    def is_healthy(self) -> bool:
        return self.ltv_cac_ratio >= 3 and self.churn_rate <= 5


class FinancialForecaster(BaseAgent):
    AGENT_ID = "financial_forecaster"
    AGENT_NAME = "Financial Forecaster 🔮"
    MODEL = "claude-sonnet-4-5"
    MAX_TOKENS = 2500

    @property
    def system_prompt(self) -> str:
        return """أنت Financial Forecaster، تتوقع المستقبل المالي.
تتابع: MRR, ARR, Churn, LTV, CAC, Burn, Runway.
تصدر تقارير: weekly, monthly, quarterly."""

    def forecast_mrr(self, current_mrr: float, growth_rate: float, churn: float, months: int = 12) -> list[float]:
        """توقع MRR للأشهر القادمة"""
        mrr = current_mrr
        forecast = []
        for _ in range(months):
            mrr = mrr * (1 + growth_rate - churn)
            forecast.append(round(mrr, 2))
        return forecast

    def calculate_runway(self, cash: float, monthly_burn: float) -> int:
        return int(cash / monthly_burn) if monthly_burn > 0 else 999


# ═════════════════════════════════════════════════════════════════════
# 4.8 Tier Designer 🎨
# ═════════════════════════════════════════════════════════════════════

TierDesigner = create_agent_class(
    agent_id="tier_designer",
    agent_name="Tier Designer 🎨",
    role_description="""أنت Tier Designer، تصمم باقات الاشتراك بدقة نفسية.
تعرف feature gating, anchoring, decoy effect.""",
    expertise="12 سنة | صمّمت باقات لـ 30+ منتج SaaS",
    output_format="""```
🎨 TIER STRUCTURE
━━━━━━━━━━━━━━━━━━━━
🌱 Micro    $15/mo  - [features]
🚀 Starter  $25/mo  - [features]
💎 Pro      $50/mo  - [features]
👑 Elite    $100/mo - [features]
```""",
    skills=[
        "Feature-to-tier mapping", "Pricing tier design", "Usage limits design",
        "Feature gating strategy", "Tier naming psychology", "Visual presentation",
        "Upgrade path optimization", "Tier consolidation", "New tier introduction",
        "Limited-time offerings", "Enterprise tier design", "Free tier optimization",
        "Comparison tables", "Feature value perception", "Tier-specific SLAs",
        "Add-on architecture", "Custom Enterprise negotiation", "Family plans",
        "Educational discounts", "Tier migration"
    ]
)


# ═════════════════════════════════════════════════════════════════════
# 4.9 Tax & Compliance 🧾
# ═════════════════════════════════════════════════════════════════════

class TaxCompliance(BaseAgent):
    AGENT_ID = "tax_compliance"
    AGENT_NAME = "Tax & Compliance 🧾"
    MODEL = "claude-sonnet-4-5"
    MAX_TOKENS = 1500

    VAT_RATES = {
        "SA": 0.15,  # Saudi Arabia
        "AE": 0.05,  # UAE
        "KW": 0.00,  # Kuwait (no VAT yet)
        "BH": 0.10,  # Bahrain
        "OM": 0.05,  # Oman
        "QA": 0.00,  # Qatar (planned)
        "EG": 0.14,  # Egypt
        "JO": 0.16,  # Jordan
        "GB": 0.20,  # UK
        "DE": 0.19,  # Germany
        "FR": 0.20,  # France
        "US": 0.00,  # varies by state
    }

    @property
    def system_prompt(self) -> str:
        return """أنت Tax & Compliance، تدير الضرائب لكل بلد.
تستخدم Lemon Squeezy (Merchant of Record) لتبسيط VAT العالمي."""

    def calculate_vat(self, amount: float, country: str) -> dict:
        rate = self.VAT_RATES.get(country.upper(), 0.0)
        vat_amount = amount * rate
        return {
            "subtotal": amount,
            "vat_rate": rate,
            "vat_amount": round(vat_amount, 2),
            "total": round(amount + vat_amount, 2),
            "country": country
        }


# ═════════════════════════════════════════════════════════════════════
# 4.10 Affiliate Commission Manager 🤝
# ═════════════════════════════════════════════════════════════════════

class AffiliateManager(BaseAgent):
    AGENT_ID = "affiliate_manager"
    AGENT_NAME = "Affiliate Manager 🤝"
    MODEL = "claude-haiku-4-5"
    MAX_TOKENS = 1200

    TIERS = {
        "bronze":  {"min_refs": 0,  "commission": 0.20, "duration": "3_months"},
        "silver":  {"min_refs": 10, "commission": 0.25, "duration": "lifetime"},
        "gold":    {"min_refs": 50, "commission": 0.30, "duration": "lifetime"},
        "diamond": {"min_refs": 100,"commission": 0.35, "duration": "lifetime"},
    }

    @property
    def system_prompt(self) -> str:
        return """أنت Affiliate Manager، تدير برنامج الإحالة بشفافية.
4 مستويات: Bronze (20%), Silver (25%), Gold (30%), Diamond (35%)."""

    def get_tier(self, referral_count: int) -> str:
        if referral_count >= 100:
            return "diamond"
        elif referral_count >= 50:
            return "gold"
        elif referral_count >= 10:
            return "silver"
        return "bronze"

    def calculate_commission(self, sale_amount: float, referral_count: int) -> dict:
        tier = self.get_tier(referral_count)
        info = self.TIERS[tier]
        commission = sale_amount * info["commission"]
        return {
            "tier": tier,
            "rate": info["commission"],
            "commission_amount": round(commission, 2),
            "duration": info["duration"]
        }


# ═════════════════════════════════════════════════════════════════════
# 4.11 Reserve Fund Manager 🏛️
# ═════════════════════════════════════════════════════════════════════

ReserveFundManager = create_agent_class(
    agent_id="reserve_fund_manager",
    agent_name="Reserve Fund Manager 🏛️",
    role_description="""أنت Reserve Fund Manager، تدير الاحتياطي المالي.
التوزيع المستهدف: 30% operating, 20% reserve, 30% growth, 20% profit.""",
    expertise="20 سنة | إدارة محافظ خزينة الشركات",
    output_format="""```
🏛️ RESERVE STATUS
━━━━━━━━━━━━━━━━━━━━
💰 Total Cash: $[X]
🏦 Operating: $[X] (30%)
🛡️  Emergency: $[X] (20%)
📈 Growth: $[X] (30%)
💎 Profit: $[X] (20%)
📅 Runway: [X] months
```""",
    skills=[
        "Reserve fund allocation", "Cash management", "Safe investments",
        "Emergency fund maintenance", "Profit distribution", "Re-investment",
        "Capital expenditure", "Working capital", "FX hedging",
        "Crypto treasury", "Stablecoin allocation", "Banking relationships",
        "Multi-bank diversification", "Interest accounts", "Liquidity ladder",
        "Financial risk management", "Insurance coverage", "Contingency planning",
        "Growth capital allocation", "Dividend policy"
    ]
)


# ═════════════════════════════════════════════════════════════════════
# 4.12 Competitor Pricing Spy 🕵️
# ═════════════════════════════════════════════════════════════════════

CompetitorPricingSpy = create_agent_class(
    agent_id="competitor_pricing_spy",
    agent_name="Competitor Pricing Spy 🕵️",
    role_description="""أنت Competitor Pricing Spy، تراقب أسعار وعروض المنافسين أسبوعياً.
المنافسون: 3Commas, Cryptohopper, Bitsgap, Pionex, Coinrule, TradeSanta.""",
    expertise="15 سنة | competitive intelligence | تتبع 200+ منافس",
    output_format="""```
🕵️ COMPETITOR REPORT
━━━━━━━━━━━━━━━━━━━━
📊 تغييرات الأسعار: [قائمة]
🆕 ميزات جديدة: [قائمة]
🎯 فرص differentiation: [قائمة]
⚠️  تهديدات: [قائمة]
💡 توصيات: [قائمة]
```""",
    skills=[
        "Competitor monitoring", "Pricing changes detection", "New competitor ID",
        "Feature comparison matrix", "Promotion tracking", "Seasonal offers",
        "New tier introductions", "Discontinued features", "Marketing message analysis",
        "Customer review sentiment", "Market positioning", "Differentiation opportunities",
        "SWOT analysis", "Pricing recommendations", "Feature gap analysis",
        "Geographic expansion tracking", "Funding/M&A news", "Quarterly reports",
        "Strategic threat assessment", "Counter-positioning"
    ]
)


# ═════════════════════════════════════════════════════════════════════
# Export
# ═════════════════════════════════════════════════════════════════════

FINANCIAL_AGENTS = {
    "pricing_strategist": PricingStrategist,
    "cost_tracker": CostTracker,
    "revenue_optimizer": RevenueOptimizer,
    "subscription_manager": SubscriptionManager,
    "payment_gateway": PaymentGatewayManager,
    "failed_payment_recovery": FailedPaymentRecovery,
    "financial_forecaster": FinancialForecaster,
    "tier_designer": TierDesigner,
    "tax_compliance": TaxCompliance,
    "affiliate_manager": AffiliateManager,
    "reserve_fund_manager": ReserveFundManager,
    "competitor_pricing_spy": CompetitorPricingSpy,
}
