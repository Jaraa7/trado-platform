/**
 * 🏛️ TradoAI — Single Source of Truth for All Tiers
 *
 * هذا الملف هو المرجع الوحيد لكل الباقات والصلاحيات.
 * يُستخدم في:
 *   - Landing Page (pricing section)
 *   - User Dashboard (feature gates)
 *   - Backend API (limits enforcement)
 *   - Admin Panel (user management)
 */

// ─── Types ────────────────────────────────────────────────────────────────────

export type TierSlug =
  | "trial"
  | "micro"
  | "starter"
  | "pro"
  | "elite"
  | "whale"
  | "institutional"
  | "founder";

export type BillingCycle = "monthly" | "annual";

export type FeatureKey =
  | "signals"
  | "alerts"
  | "whale_tracker"
  | "opportunity_hunter"
  | "auto_execute"
  | "backtesting"
  | "strategy_builder"
  | "portfolio_manager"
  | "multi_portfolio"
  | "custom_risk_limits"
  | "api_access"
  | "tax_reporting"
  | "early_signals"
  | "dedicated_manager"
  | "strategy_calls"
  | "daily_reports"
  | "white_label"
  | "sub_accounts"
  | "compliance_reports"
  | "sla_99_9"
  | "founder_badge"
  | "roadmap_voting";

export type StrategyId =
  | "trend_following"
  | "breakout"
  | "mean_reversion"
  | "scalping"
  | "custom"
  | "multi_strategy"
  | "institutional";

export type MarketType =
  | "spot"
  | "futures"
  | "perpetuals"
  | "options"
  | "defi"
  | "cfd";

export interface TierConfig {
  slug:         TierSlug;
  name:         string;
  price_monthly: number;          // 0 = free
  price_annual:  number | null;   // null = annual not available
  badge:         string | null;
  popular:       boolean;
  color:         string;          // للـ UI

  // ─── Limits ──────────────────────────────────────────────────────
  signals_per_day:  number;       // -1 = unlimited
  exchanges:        number;       // -1 = unlimited
  pairs:            number;       // -1 = unlimited
  seats:            number;       // -1 = unlimited (للـ Institutional/Founder)

  // ─── Features (boolean gates) ────────────────────────────────────
  features: FeatureKey[];

  // ─── Strategies ──────────────────────────────────────────────────
  strategies: StrategyId[];

  // ─── Markets ─────────────────────────────────────────────────────
  markets: MarketType[];

  // ─── Support ─────────────────────────────────────────────────────
  support_response_hours: number | null; // null = no support, 0 = 24/7

  // ─── Display (for pricing page) ──────────────────────────────────
  highlights: Record<string, string[]>; // locale → feature list strings
}

// ─── Tier Definitions ─────────────────────────────────────────────────────────

export const TIERS: Record<TierSlug, TierConfig> = {

  trial: {
    slug: "trial",
    name: "Trial",
    price_monthly: 0,
    price_annual:  0,
    badge: "7 days free",
    popular: false,
    color: "#94a3b8",
    signals_per_day: 3,
    exchanges: 1,
    pairs: 5,
    seats: 1,
    features: ["signals", "alerts"],
    strategies: ["trend_following"],
    markets: ["spot"],
    support_response_hours: null,
    highlights: {
      en: ["3 signals/day", "1 exchange", "All 87 AI tools", "Telegram alerts", "No credit card"],
      ar: ["3 إشارات/يوم", "منصة واحدة", "كل 87 أداة AI", "تنبيهات Telegram", "بدون بطاقة ائتمان"],
    },
  },

  micro: {
    slug: "micro",
    name: "Micro",
    price_monthly: 29,
    price_annual:  290,
    badge: null,
    popular: false,
    color: "#6ee7b7",
    signals_per_day: 5,
    exchanges: 1,
    pairs: 10,
    seats: 1,
    features: ["signals", "alerts"],
    strategies: ["trend_following", "breakout"],
    markets: ["spot"],
    support_response_hours: null,
    highlights: {
      en: ["5 signals/day", "1 exchange", "All 87 AI tools", "Telegram alerts", "Knowledge base"],
      ar: ["5 إشارات/يوم", "منصة واحدة", "كل 87 أداة AI", "تنبيهات Telegram", "قاعدة المعرفة"],
    },
  },

  starter: {
    slug: "starter",
    name: "Starter",
    price_monthly: 59,
    price_annual:  590,
    badge: null,
    popular: false,
    color: "#34d399",
    signals_per_day: 15,
    exchanges: 2,
    pairs: 20,
    seats: 1,
    features: ["signals", "alerts", "whale_tracker", "opportunity_hunter"],
    strategies: ["trend_following", "breakout", "mean_reversion"],
    markets: ["spot", "futures"],
    support_response_hours: 12,
    highlights: {
      en: ["15 signals/day", "2 exchanges", "Whale Tracker", "Opportunity Hunter", "Sentiment dashboard", "12h support"],
      ar: ["15 إشارة/يوم", "منصتان", "Whale Tracker", "صيد الفرص", "لوحة المعنويات", "دعم 12 ساعة"],
    },
  },

  pro: {
    slug: "pro",
    name: "Pro",
    price_monthly: 99,
    price_annual:  990,
    badge: "Most Popular",
    popular: true,
    color: "#10b981",
    signals_per_day: 50,
    exchanges: 3,
    pairs: 50,
    seats: 1,
    features: [
      "signals", "alerts", "whale_tracker", "opportunity_hunter",
      "backtesting", "strategy_builder", "portfolio_manager",
    ],
    strategies: ["trend_following", "breakout", "mean_reversion", "scalping", "custom"],
    markets: ["spot", "futures", "perpetuals"],
    support_response_hours: 1,
    highlights: {
      en: ["50 signals/day", "3 exchanges", "Backtesting", "Strategy builder", "Portfolio manager", "Weekly PDF report", "1h support"],
      ar: ["50 إشارة/يوم", "3 منصات", "Backtesting", "بناء استراتيجية", "مدير المحفظة", "تقرير PDF أسبوعي", "دعم ساعة"],
    },
  },

  elite: {
    slug: "elite",
    name: "Elite",
    price_monthly: 199,
    price_annual:  1990,
    badge: null,
    popular: false,
    color: "#0ea5e9",
    signals_per_day: 150,
    exchanges: 5,
    pairs: -1,
    seats: 1,
    features: [
      "signals", "alerts", "whale_tracker", "opportunity_hunter",
      "auto_execute", "backtesting", "strategy_builder",
      "portfolio_manager", "multi_portfolio", "custom_risk_limits",
      "api_access", "tax_reporting",
    ],
    strategies: ["trend_following", "breakout", "mean_reversion", "scalping", "custom", "multi_strategy"],
    markets: ["spot", "futures", "perpetuals", "options"],
    support_response_hours: 0.25, // 15 min
    highlights: {
      en: ["150 signals/day", "5 exchanges", "Unlimited pairs", "Auto-Execute", "API access", "Tax reporting", "Custom risk limits", "15min support"],
      ar: ["150 إشارة/يوم", "5 منصات", "أزواج غير محدودة", "تنفيذ تلقائي", "API access", "تقارير ضريبية", "حدود مخاطر مخصصة", "دعم 15 دقيقة"],
    },
  },

  whale: {
    slug: "whale",
    name: "Whale",
    price_monthly: 499,
    price_annual:  4990,
    badge: "🐋",
    popular: false,
    color: "#6366f1",
    signals_per_day: -1,
    exchanges: 10,
    pairs: -1,
    seats: 1,
    features: [
      "signals", "alerts", "whale_tracker", "opportunity_hunter",
      "auto_execute", "backtesting", "strategy_builder",
      "portfolio_manager", "multi_portfolio", "custom_risk_limits",
      "api_access", "tax_reporting", "early_signals",
      "dedicated_manager", "strategy_calls", "daily_reports",
    ],
    strategies: ["trend_following", "breakout", "mean_reversion", "scalping", "custom", "multi_strategy", "institutional"],
    markets: ["spot", "futures", "perpetuals", "options", "defi"],
    support_response_hours: 0, // 24/7
    highlights: {
      en: ["Unlimited signals", "10 exchanges", "Dedicated account manager", "Weekly strategy call", "Daily AI reports", "Early signals", "Custom strategy"],
      ar: ["إشارات غير محدودة", "10 منصات", "مدير حساب مخصص", "مكالمة أسبوعية", "تقارير يومية", "إشارات مبكرة", "استراتيجية مخصصة"],
    },
  },

  institutional: {
    slug: "institutional",
    name: "Institutional",
    price_monthly: 1499,
    price_annual:  14990,
    badge: "🏛️",
    popular: false,
    color: "#a78bfa",
    signals_per_day: -1,
    exchanges: -1,
    pairs: -1,
    seats: -1,
    features: [
      "signals", "alerts", "whale_tracker", "opportunity_hunter",
      "auto_execute", "backtesting", "strategy_builder",
      "portfolio_manager", "multi_portfolio", "custom_risk_limits",
      "api_access", "tax_reporting", "early_signals",
      "dedicated_manager", "strategy_calls", "daily_reports",
      "white_label", "sub_accounts", "compliance_reports", "sla_99_9",
    ],
    strategies: ["trend_following", "breakout", "mean_reversion", "scalping", "custom", "multi_strategy", "institutional"],
    markets: ["spot", "futures", "perpetuals", "options", "defi", "cfd"],
    support_response_hours: 0, // 24/7
    highlights: {
      en: ["Unlimited everything", "White-label dashboard", "5 sub-accounts", "99.9% SLA", "Compliance reports", "Direct API", "24/7 dedicated manager"],
      ar: ["كل شيء غير محدود", "Dashboard باسمك", "5 حسابات فرعية", "SLA 99.9%", "تقارير الامتثال", "API مباشر", "مدير مخصص 24/7"],
    },
  },

  founder: {
    slug: "founder",
    name: "Founder",
    price_monthly: 2999,
    price_annual:  null,  // annual billing only (monthly rate)
    badge: "👑 100 seats only",
    popular: false,
    color: "#fbbf24",
    signals_per_day: -1,
    exchanges: -1,
    pairs: -1,
    seats: 100, // hard limit — 100 founders total
    features: [
      "signals", "alerts", "whale_tracker", "opportunity_hunter",
      "auto_execute", "backtesting", "strategy_builder",
      "portfolio_manager", "multi_portfolio", "custom_risk_limits",
      "api_access", "tax_reporting", "early_signals",
      "dedicated_manager", "strategy_calls", "daily_reports",
      "white_label", "sub_accounts", "compliance_reports", "sla_99_9",
      "founder_badge", "roadmap_voting",
    ],
    strategies: ["trend_following", "breakout", "mean_reversion", "scalping", "custom", "multi_strategy", "institutional"],
    markets: ["spot", "futures", "perpetuals", "options", "defi", "cfd"],
    support_response_hours: 0,
    highlights: {
      en: ["Everything in Institutional", "Lifetime price lock", "Founding member badge", "Shape our roadmap", "All future features free", "Annual in-person summit"],
      ar: ["كل مزايا Institutional", "سعر مثبّت للأبد", "شارة المؤسس", "تشكيل خارطة الطريق", "كل الميزات المستقبلية مجاناً", "قمة سنوية حضورية"],
    },
  },
};

// ─── Helper Functions ─────────────────────────────────────────────────────────

/** هل لدى المستخدم ميزة معينة؟ */
export function hasFeature(tier: TierSlug, feature: FeatureKey): boolean {
  return TIERS[tier]?.features.includes(feature) ?? false;
}

/** هل لدى المستخدم استراتيجية معينة؟ */
export function hasStrategy(tier: TierSlug, strategy: StrategyId): boolean {
  return TIERS[tier]?.strategies.includes(strategy) ?? false;
}

/** هل يمكن إضافة منصة أخرى؟ */
export function canAddExchange(tier: TierSlug, current: number): boolean {
  const max = TIERS[tier]?.exchanges ?? 1;
  return max === -1 || current < max;
}

/** هل يمكن إضافة زوج آخر؟ */
export function canAddPair(tier: TierSlug, current: number): boolean {
  const max = TIERS[tier]?.pairs ?? 5;
  return max === -1 || current < max;
}

/** هل الباقة تدعم Auto-Execute؟ ($199+) */
export function canAutoExecute(tier: TierSlug): boolean {
  return hasFeature(tier, "auto_execute");
}

/** سعر الباقة الشهري (أو السنوي مقسوماً على 12) */
export function getDisplayPrice(tier: TierSlug, cycle: BillingCycle): number {
  const t = TIERS[tier];
  if (!t) return 0;
  if (cycle === "annual" && t.price_annual !== null) {
    return Math.floor(t.price_annual / 12);
  }
  return t.price_monthly;
}

/** قائمة الباقات بالترتيب */
export const TIER_ORDER: TierSlug[] = [
  "trial", "micro", "starter", "pro", "elite", "whale", "institutional", "founder"
];

/** الباقات في الصف الأول (Landing Page) */
export const TIER_ROW_1: TierSlug[] = ["trial", "micro", "starter", "pro"];

/** الباقات في الصف الثاني (Landing Page) */
export const TIER_ROW_2: TierSlug[] = ["elite", "whale", "institutional", "founder"];
