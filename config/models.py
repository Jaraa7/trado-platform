"""
config/models.py — المصدر الوحيد للحقيقة عن النماذج وأسعارها وتوجيهها.

لا يُكتب اسم نموذج في أي ملف آخر. الوكلاء يعلنون فئة (TIER) فقط،
والموجّه في core/llm_router.py يحوّل الفئة إلى نموذج وقت الاستدعاء.

الأسعار: دولار لكل مليون توكن. PRICES_AS_OF = تاريخ آخر تحقق؛
تُراجع ربع سنويًا وأي تغيير يخل بالمفاضلة يصل كقرار من الدرجة 1.
"""
from __future__ import annotations

PRICES_AS_OF = "2026-10-04"

# provider:model_id → {input, output}
MODELS: dict[str, dict] = {
    "anthropic:claude-sonnet-5":        {"input": 2.00,  "output": 10.00, "max_tokens": 8192},
    "anthropic:claude-opus-5-5":        {"input": 4.00,  "output": 20.00, "max_tokens": 8192},
    "anthropic:claude-haiku-4-5":       {"input": 1.00,  "output": 5.00,  "max_tokens": 4096},
    "deepseek:deepseek-chat":           {"input": 0.435, "output": 0.87,  "max_tokens": 8192},   # V4-Pro
    "deepseek:deepseek-flash":          {"input": 0.14,  "output": 0.28,  "max_tokens": 8192},   # V4-Flash
    "google:gemini-3.1-pro":            {"input": 2.00,  "output": 12.00, "max_tokens": 8192},
    "google:gemini-3.5-flash-lite":     {"input": 0.30,  "output": 2.50,  "max_tokens": 8192},
}

# الفئة → [الأساسي, البديل من مزود مختلف]
TIERS: dict[str, list[str]] = {
    "frontier": ["anthropic:claude-sonnet-5", "google:gemini-3.1-pro"],
    "standard": ["deepseek:deepseek-chat", "google:gemini-3.1-pro"],
    "cheap":    ["deepseek:deepseek-flash", "google:gemini-3.5-flash-lite"],
}

# التنزيل عند تجاوز الميزانية
DOWNGRADE = {"frontier": "standard", "standard": "cheap", "cheap": None}

# نقاط النهاية المتوافقة مع OpenAI (DeepSeek وGemini)
OPENAI_COMPAT_BASE = {
    "deepseek": "https://api.deepseek.com/v1",
    "google":   "https://generativelanguage.googleapis.com/v1beta/openai",
}

# توافق خلفي: معرفات قديمة في الكود → المفتاح الجديد
LEGACY_ALIASES = {
    "claude-sonnet-4-5": "anthropic:claude-sonnet-5",
    "claude-haiku-4-5":  "anthropic:claude-haiku-4-5",
}


def resolve(model_key: str) -> str:
    return LEGACY_ALIASES.get(model_key, model_key)


def cost_usd(model_key: str, input_tokens: int, output_tokens: int) -> float:
    p = MODELS.get(resolve(model_key), {"input": 3.0, "output": 15.0})
    return round(input_tokens / 1e6 * p["input"] + output_tokens / 1e6 * p["output"], 6)
