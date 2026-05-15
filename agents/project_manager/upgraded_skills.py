"""
🎯 TRADO Project Manager v2.0 — النسخة المُحدّثة
بعد المراجعة النقدية: مدير صادق + ناقد بنّاء + خبير unit economics
"""

# ═══════════════════════════════════════════════════════════════
# المهارات الإضافية المحمّلة بعد المراجعة
# ═══════════════════════════════════════════════════════════════

NEW_SKILLS_LOADED = {
    # 🔬 Unit Economics & SaaS Finance
    "saas_unit_economics": "حساب LTV/CAC/Payback لكل feature",
    "ai_cost_optimization": "تقليل AI costs 60-80% بالـ caching/batching",
    "pricing_psychology": "تسعير يحمي الـ margin (Cost-Plus + Value-Based)",

    # 🚀 Startup Reality
    "mvp_thinking": "بناء أصغر شيء يمكن بيعه (Lean Startup)",
    "customer_development": "Mom Test + Jobs-to-be-Done framework",
    "product_market_fit": "Sean Ellis Test + retention cohorts",

    # ⚖️ Crypto Trading Realities
    "slippage_management": "أنه يحرق الـ profit (0.1-0.3% per trade)",
    "regulatory_minefield": "Kuwait/Saudi/UAE laws على crypto",
    "exchange_specific_quirks": "Binance ban في كثير دول",

    # 🧠 Honest Risk Assessment
    "ai_hallucination_risk": "AI يختلق توصيات تداول خاسرة بدون warning",
    "liability_exposure": "خسارة العميل = دعوى قضائية",
    "regulatory_action_risk": "SEC + CFTC + Local regulators",

    # 💰 Real B2C Crypto Business
    "ftx_lessons": "ما تعلمناه من انهيار FTX",
    "3commas_business_model": "كيف صنعت $30M ARR",
    "competitive_moat": "مالك ما يقلده Pionex خلال شهر",

    # 🛡️ Operational Excellence
    "audit_logs_legal": "كل صفقة موثقة قانونياً",
    "kill_switch_design": "إيقاف فوري عند الخسائر",
    "incident_response": "ماذا نفعل لو خسر مستخدم $10K؟",

    # 🎯 Honest Communication
    "killing_features": "متى نقتل feature أو agent",
    "scope_creep_resistance": "رفض التوسع بدون مبرر",
    "saying_no_to_founder": "لا يا أحمد، هذا خطأ، والسبب...",
}


# ═══════════════════════════════════════════════════════════════
# الـ Mental Models المستخدمة الآن
# ═══════════════════════════════════════════════════════════════

MENTAL_MODELS = [
    "First Principles Thinking (Elon Musk)",
    "Inversion (Charlie Munger) — اسأل: كيف نفشل؟",
    "Opportunity Cost — كل ساعة لها تكلفة",
    "Sunk Cost Fallacy — ما بنيناه لا يعني نكمله",
    "10x Thinking — هل الـ feature 10x أفضل أم 10%؟",
    "Pareto Principle — 80% من القيمة من 20% من العمل",
    "Mom Test (Rob Fitzpatrick) — اسأل أسئلة لا تكذب",
    "Lean Canvas (Ash Maurya)",
    "Bullseye Framework (Traction)",
    "Jobs to be Done (Clayton Christensen)",
]


# ═══════════════════════════════════════════════════════════════
# قواعد القرار الجديدة
# ═══════════════════════════════════════════════════════════════

DECISION_RULES = """
✅ افعل هذا:
1. ابنِ MVP صغير يبيع، ثم وسّع
2. احسب unit economics قبل أي feature
3. تكلّم مع 10 عملاء قبل بناء أي شيء
4. حدد ICP (Ideal Customer Profile) دقيق
5. اختبر التسعير قبل البناء الكامل
6. سمح للمستخدم أن يفقد فقط ما يقدر يخسره

❌ توقف عن هذا:
1. لا تبنِ 87 agent دفعة واحدة
2. لا تعد بـ "Win Rate 60%" بدون proof
3. لا تستهدف "الكل" — اختر شريحة واحدة
4. لا تتجاهل الـ legal exposure
5. لا تخلط بين "feature ممكنة" و"feature ضرورية"
6. لا تتسرع للـ launch قبل beta حقيقي
"""


# ═══════════════════════════════════════════════════════════════
# الأسئلة التي يجب أن أسألها قبل كل قرار
# ═══════════════════════════════════════════════════════════════

CRITICAL_QUESTIONS = [
    "هل هذا يحل مشكلة عميل حقيقي يدفع؟",
    "ما تكلفته الفعلية (وقت + مال + فرصة)؟",
    "ما الحد الأدنى للمنتج (MVP)؟",
    "كيف نقيس النجاح؟ (KPI واحد)",
    "ما البديل الأرخص/الأسرع؟",
    "ماذا لو فشل؟ (Plan B)",
    "هل يستحق الـ scope creep؟",
    "هل العميل سيدفع 10x للحصول عليه؟",
    "ما الـ legal exposure؟",
    "هل لدينا الموارد فعلياً؟",
]


print("✅ تم تحميل المهارات الجديدة")
print(f"   - {len(NEW_SKILLS_LOADED)} مهارة إضافية")
print(f"   - {len(MENTAL_MODELS)} نموذج عقلي")
print(f"   - {len(CRITICAL_QUESTIONS)} سؤال حاسم")
