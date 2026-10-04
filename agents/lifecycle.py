"""
agents/lifecycle.py — حالة كل وكيل وفئة نموذجه (مراجعة أكتوبر 2026).

status:
  active     يعمل ويُستدعى
  tool_backed يعمل لكنه يقرأ مخرجات أداة حتمية (الحقل tool) ولا يكون مصدر الحقيقة
  merged     أُدمج في وكيل آخر (الحقل into) — استدعاؤه يُحوَّل تلقائيًا
  parked     معلّق: مسجَّل، لا يُستدعى، يُفعَّل بتغيير سطر واحد هنا
  removed    مُستغنى عنه نهائيًا
tier: frontier | standard | cheap  (التوجيه في config/models.py)

غير المذكور هنا = active/standard (الافتراضي).
"""
from __future__ import annotations

LIFECYCLE: dict[str, dict] = {
    # ── 1. نواة التداول: تبقى وتُقوّى ───────────────────────────────
    "scanner_pro":          {"status": "active", "tier": "cheap"},
    "analyst_master":       {"status": "active", "tier": "frontier"},
    "risk_guardian":        {"status": "active", "tier": "standard", "note": "الحساب الحتمي يقرر؛ النموذج يشرح"},
    "executioner_pro":      {"status": "active", "tier": "cheap"},
    "regime_detector":      {"status": "tool_backed", "tool": "nervous.market.classify_regime", "tier": "cheap"},
    "pattern_recognition":  {"status": "active", "tier": "cheap", "note": "يحتاج تغذية شموع من nervous.market"},
    "news_analyst":         {"status": "active", "tier": "standard"},
    "sentiment_analyzer":   {"status": "active", "tier": "cheap"},
    "whale_tracker":        {"status": "active", "tier": "cheap"},
    "strategy_designer":    {"status": "active", "tier": "frontier"},
    "portfolio_manager":    {"status": "active", "tier": "standard", "note": "يُربط بمراكز Bybit الفعلية"},
    "macro_economist":      {"status": "active", "tier": "standard"},
    "observatory":          {"status": "active", "tier": "cheap"},

    # ── 2. يُستبدل بأداة حتمية ──────────────────────────────────────
    "backtester_pro":       {"status": "tool_backed", "tool": "freqtrade", "tier": "standard"},
    "penetration_tester":   {"status": "tool_backed", "tool": "bandit+pip-audit", "tier": "standard"},
    "vulnerability_scanner":{"status": "tool_backed", "tool": "pip-audit+dependabot", "tier": "cheap"},
    "security_auditor":     {"status": "tool_backed", "tool": "bandit", "tier": "standard"},
    "ddos_shield":          {"status": "tool_backed", "tool": "cloudflare", "tier": "cheap"},
    "cost_tracker":         {"status": "tool_backed", "tool": "nervous_metrics", "tier": "cheap"},
    "feature_prioritizer":  {"status": "tool_backed", "tool": "nervous.goals", "tier": "standard"},
    "market_researcher":    {"status": "tool_backed", "tool": "nervous.market", "tier": "standard"},

    # ── 3. يُدمج ─────────────────────────────────────────────────────
    "chatbot_free":         {"status": "merged", "into": "support_pro"},
    "chatbot_micro":        {"status": "merged", "into": "support_pro"},
    "chatbot_starter":      {"status": "merged", "into": "support_pro"},
    "chatbot_pro":          {"status": "merged", "into": "support_pro"},
    "chatbot_elite":        {"status": "merged", "into": "support_pro"},
    "competitor_pricing_spy": {"status": "merged", "into": "competitor_analyst"},
    "tier_designer":        {"status": "merged", "into": "pricing_strategist"},
    "revenue_optimizer":    {"status": "merged", "into": "pricing_strategist"},
    "cost_optimizer":       {"status": "merged", "into": "cost_tracker"},
    "affiliate_relations":  {"status": "merged", "into": "affiliate_manager"},
    "project_manager_ops":  {"status": "merged", "into": "master_orchestrator"},
    "code_reviewer":        {"status": "merged", "into": "bug_hunter"},
    "test_engineer":        {"status": "merged", "into": "bug_hunter"},

    # ── 4. يبقى بشرط الأدوات ─────────────────────────────────────────
    "support_pro":          {"status": "active", "tier": "cheap", "note": "وكيل الدعم الموحد؛ الباقة معامل"},
    "retention_specialist": {"status": "active", "tier": "standard"},
    "failed_payment_recovery": {"status": "active", "tier": "cheap"},
    "onboarding_specialist":{"status": "active", "tier": "cheap"},
    "telegram_master":      {"status": "active", "tier": "cheap"},
    "twitter_manager":      {"status": "active", "tier": "standard"},
    "content_creator":      {"status": "active", "tier": "standard"},
    "reporter":             {"status": "active", "tier": "frontier", "note": "تقرير الجمعة"},
    "devops_monitor":       {"status": "tool_backed", "tool": "sentry", "tier": "cheap"},
    "bug_hunter":           {"status": "active", "tier": "frontier", "note": "نواة وكيل التطوير الليلي"},
    "competitor_analyst":   {"status": "active", "tier": "standard"},
    "pricing_strategist":   {"status": "active", "tier": "frontier"},
    "product_manager":      {"status": "active", "tier": "frontier"},
    "master_orchestrator":  {"status": "tool_backed", "tool": "nervous brain", "tier": "frontier"},
    "subscription_manager": {"status": "active", "tier": "cheap"},

    # ── 5. معلّق الآن ────────────────────────────────────────────────
    **{k: {"status": "parked"} for k in [
        "brand_designer", "graphic_designer", "infographic_creator", "logo_designer",
        "motion_designer", "video_editor", "ui_ux_designer",
        "instagram_manager", "tiktok_manager", "youtube_producer", "linkedin_manager",
        "influencer_outreach", "ad_campaign_manager", "email_marketing", "growth_hacker", "seo_specialist",
        "hr_team_manager", "reserve_fund_manager", "financial_forecaster", "ab_testing_manager",
        "gap_analyzer", "user_researcher", "payment_gateway", "api_integration", "frontend_developer",
        "backend_master", "database_specialist", "code_architect", "devops_engineer", "performance_tuner",
        "compliance_officer", "arbitrage_hunter", "affiliate_manager", "anti_fraud", "crypto_defender",
        "community_manager", "feedback_collector",
    ]},

    # ── 6. مُستغنى عنه ───────────────────────────────────────────────
    "tax_compliance":       {"status": "removed", "note": "الضرائب لمحاسب بشري لا لنموذج لغوي"},
}

DEFAULT = {"status": "active", "tier": "standard"}


def info(agent_id: str) -> dict:
    return {**DEFAULT, **LIFECYCLE.get(agent_id, {})}


def resolve_alias(agent_id: str) -> str:
    """وكيل مدمج → الوكيل الذي يحل محله (يتبع السلسلة)."""
    seen = set()
    while True:
        meta = LIFECYCLE.get(agent_id, {})
        if meta.get("status") != "merged" or agent_id in seen:
            return agent_id
        seen.add(agent_id)
        agent_id = meta["into"]
