"""llm_judge brain: Gemini (cheap tier) decides long/short/none on hourly bars, LIVE bars only.

- one call per (symbol, bar) shared by all llm_judge managers (cache)
- hard caps: calls per hour and the shared monthly LLM cap (t100_llm_costs); beyond them -> None
  (the family then simply doesn't open; the Risk Guardian still vets every signal)
- any failure -> None. Never raises into the trading loop.
"""
from __future__ import annotations
import json, os, re
from datetime import datetime, timezone
from typing import Callable, Optional
import numpy as np
from loguru import logger

HOUR_MS = 3_600_000
MAX_CALLS_PER_HOUR = int(os.getenv("T100_JUDGE_CALLS_PER_HOUR", "40"))
CAP_USD = float(os.getenv("T100_LLM_CAP_USD", "150"))
SYSTEM = ("You are a cautious crypto perp trader's signal filter. Given recent hourly-ish closes (as % returns), "
          "funding and sentiment, answer ONLY JSON {\"side\":\"long\"|\"short\"|\"none\"}. "
          "Prefer none unless the setup is clear.")


def default_llm(system: str, user: str):
    from core.llm_router import LLMRouter
    r = LLMRouter().complete("cheap", system, [{"role": "user", "content": user}], agent_id="t100_judge",
                             max_tokens=60, force_model="google:gemini-3.5-flash-lite")
    return r.text, r.model, r.input_tokens, r.output_tokens, r.cost_usd


class Judge:
    def __init__(self, store, llm: Callable = default_llm, cap: float = CAP_USD):
        self.store, self.llm, self.cap = store, llm, cap
        self.cache: dict = {}
        self.calls: dict = {}

    def __call__(self, closes, ctx) -> Optional[str]:
        sym, ts = ctx.get("sym"), ctx.get("ts")
        if not ctx.get("live") or sym is None or ts is None or ts % HOUR_MS:
            return None
        key = (sym, ts)
        if key in self.cache:
            return self.cache[key]
        hour = ts // HOUR_MS
        if self.calls.get(hour, 0) >= MAX_CALLS_PER_HOUR:
            return None
        res = None
        try:
            ym = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m")
            if self.store.month_llm_cost(ym) >= self.cap:
                return None
            c = np.asarray(closes, float)
            rets = [round(float(x) * 100, 2) for x in np.diff(c) / c[:-1]][-40:]
            user = json.dumps({"symbol": sym, "returns_pct": rets, "funding": ctx.get("funding"),
                               "sentiment": ctx.get("sentiment")})
            self.calls[hour] = self.calls.get(hour, 0) + 1
            text, model, it, ot, cost = self.llm(SYSTEM, user)
            self.store.add_llm_cost({"agent": "t100_judge", "model": model, "input_tokens": it,
                                     "output_tokens": ot, "cost_usd": cost})
            m = re.search(r'"side"\s*:\s*"(long|short|none)"', text)
            res = m.group(1) if m and m.group(1) != "none" else None
        except Exception as e:  # noqa: BLE001
            logger.warning(f"judge failed: {e}")
        if len(self.cache) > 500:
            self.cache.clear()
        self.cache[key] = res
        return res
