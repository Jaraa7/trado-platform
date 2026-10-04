"""
core/llm_router.py — موجّه النماذج حسب الفئة، مع بديل تلقائي وتسجيل تكلفة.

complete(tier, system, messages) →
  1. يختار الأساسي للفئة (أو ما يفرضه NERVOUS_FORCE_MODEL للاختبار)
  2. عند الفشل ينتقل للبديل من مزود مختلف
  3. عند تجاوز ميزانية الوكيل اليومية يُنزَّل الفئة
  4. يسجّل كل استدعاء في nervous_metrics (best-effort، لا يُفشل الاستدعاء)
لا يتخذ أي قرار مالي؛ هو قناة فقط.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Callable, Optional

from loguru import logger

from config.models import TIERS, MODELS, DOWNGRADE, OPENAI_COMPAT_BASE, cost_usd, resolve


@dataclass
class LLMResult:
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int
    fallback_used: bool


class BudgetExceeded(RuntimeError):
    pass


class LLMRouter:
    def __init__(self, caller: Optional[Callable] = None, metrics_sink: Optional[Callable] = None,
                 budget_check: Optional[Callable[[str], bool]] = None):
        """
        caller(model_key, system, messages, max_tokens) → (text, in_tok, out_tok)
          (يُستبدل في الاختبارات؛ الافتراضي يستدعي المزودين فعليًا)
        metrics_sink(dict) → يكتب في nervous_metrics
        budget_check(agent_id) → True إذا تجاوز الوكيل ميزانيته اليومية
        """
        self._caller = caller or self._default_caller
        self._sink = metrics_sink or self._default_sink
        self._budget_exceeded = budget_check or (lambda agent_id: False)

    # ── الاختيار ────────────────────────────────────────────────────
    @staticmethod
    def candidates(tier: str, force_model: Optional[str] = None) -> list[str]:
        forced = force_model or os.getenv("NERVOUS_FORCE_MODEL")
        if forced:
            return [resolve(forced)]
        if tier not in TIERS:
            raise ValueError(f"فئة غير معروفة: {tier}")
        return list(TIERS[tier])

    def effective_tier(self, tier: str, agent_id: str) -> str:
        t = tier
        while t and self._budget_exceeded(agent_id):
            nxt = DOWNGRADE.get(t)
            if nxt is None:
                raise BudgetExceeded(f"{agent_id}: تجاوز الميزانية حتى في الفئة cheap")
            logger.warning(f"⬇️ {agent_id}: تنزيل {t} → {nxt} بسبب الميزانية")
            t = nxt
        return t

    # ── الاستدعاء ───────────────────────────────────────────────────
    def complete(self, tier: str, system: str, messages: list[dict], agent_id: str = "system",
                 max_tokens: Optional[int] = None, force_model: Optional[str] = None) -> LLMResult:
        tier = self.effective_tier(tier, agent_id)
        errors = []
        for i, model_key in enumerate(self.candidates(tier, force_model)):
            t0 = time.time()
            try:
                mt = max_tokens or MODELS.get(model_key, {}).get("max_tokens", 4096)
                text, itok, otok = self._caller(model_key, system, messages, mt)
                res = LLMResult(text, model_key, itok, otok, cost_usd(model_key, itok, otok),
                                int((time.time() - t0) * 1000), fallback_used=i > 0)
                self._record(agent_id, res, ok=True)
                return res
            except Exception as ex:  # noqa: BLE001 — أي فشل → البديل
                errors.append(f"{model_key}: {type(ex).__name__}: {str(ex)[:120]}")
                self._record(agent_id, LLMResult("", model_key, 0, 0, 0.0, int((time.time() - t0) * 1000), i > 0), ok=False)
                logger.warning(f"⚠️ {agent_id}: فشل {model_key}، أجرّب البديل — {errors[-1]}")
        raise RuntimeError(f"كل النماذج فشلت للفئة {tier}: {errors}")

    # ── المزودون الفعليون ─────────────────────────────────────────────
    @staticmethod
    def _default_caller(model_key: str, system: str, messages: list[dict], max_tokens: int):
        provider, model = model_key.split(":", 1)
        if provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
            r = client.messages.create(model=model, max_tokens=max_tokens, system=system, messages=messages)
            return r.content[0].text, r.usage.input_tokens, r.usage.output_tokens
        if provider in OPENAI_COMPAT_BASE:
            import httpx
            key = os.getenv("DEEPSEEK_API_KEY" if provider == "deepseek" else "GEMINI_API_KEY", "")
            if not key:
                raise RuntimeError(f"مفتاح {provider} غير مضبوط")
            body = {"model": model, "max_tokens": max_tokens,
                    "messages": [{"role": "system", "content": system}] + messages}
            r = httpx.post(f"{OPENAI_COMPAT_BASE[provider]}/chat/completions", json=body,
                           headers={"Authorization": f"Bearer {key}"}, timeout=60)
            r.raise_for_status()
            d = r.json()
            u = d.get("usage", {})
            return (d["choices"][0]["message"]["content"],
                    int(u.get("prompt_tokens", 0)), int(u.get("completion_tokens", 0)))
        raise ValueError(f"مزود غير معروف: {provider}")

    # ── التسجيل ──────────────────────────────────────────────────────
    def _record(self, agent_id: str, res: LLMResult, ok: bool):
        try:
            self._sink({"name": "llm_call", "value": res.cost_usd,
                        "dims": {"agent": agent_id, "model": res.model, "in": res.input_tokens,
                                 "out": res.output_tokens, "ms": res.latency_ms,
                                 "ok": ok, "fallback": res.fallback_used}})
        except Exception as ex:  # noqa: BLE001
            logger.debug(f"metrics sink skipped: {ex}")

    @staticmethod
    def _default_sink(row: dict):
        if not os.getenv("NERVOUS_METRICS_ENABLED", "").lower() in ("1", "true"):
            return
        from db.client import get_supabase
        get_supabase(service_role=True).table("nervous_metrics").insert(row).execute()


_router: Optional[LLMRouter] = None


def get_router() -> LLMRouter:
    global _router
    if _router is None:
        from governance.budget import AIBudget
        _router = LLMRouter(budget_check=AIBudget().exceeded)
    return _router
