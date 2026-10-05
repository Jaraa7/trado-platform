"""
nervous/scheduler.py — الحلقة التي تبدأ عدّ الـ75 يومًا.

كل ساعة (tick):
  0. kill switch؟ → لا شيء يُنفَّذ، فقط تسجيل.
  1. أداة السوق → brief (نظام، تقلب، محركات، وضعية).
  2. أداة الأداء → توصيات مصنّفة 0/1/2.
  3. كل توصية تُسجَّل في DecisionLog:
       0 → تُنفَّذ (قائمة الرموز المستبعدة/الوكلاء الموقوفين في Redis)
       1 → تُنفَّذ + إشعار تيليجرام
       2 → إشعار بطلب موافقة
  4. انتهاء صلاحية قرارات الدرجة 2 القديمة.
  5. تحذير ميزانية الـ AI عند 80%.
كل يوم 06:00 UTC: ملخص يومي. كل جمعة 12:00 UTC: تقرير الأسبوع.

تشغيل: python -m nervous.scheduler   (process group "brain" في fly.toml)
كل ما هنا حتمي؛ الوكلاء الـLLM يُستدعون من pipeline التداول لا من هنا.
"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Callable, Optional

from loguru import logger

from governance.killswitch import KillSwitch
from governance.budget import AIBudget
from nervous.decisions import DecisionLog
from nervous.market import MarketResearch
from nervous.performance import PerformanceTracker

EXCLUDED_SYMBOLS_KEY = "nervous:excluded_symbols"
PAUSED_AGENTS_KEY = "nervous:paused_agents"
SIZE_MULT_KEY = "nervous:size_multiplier"


class Brain:
    def __init__(self, *, killswitch: Optional[KillSwitch] = None, budget: Optional[AIBudget] = None,
                 decisions: Optional[DecisionLog] = None, market: Optional[MarketResearch] = None,
                 tracker_factory: Optional[Callable[[], PerformanceTracker]] = None,
                 notify: Optional[Callable[[str], None]] = None, state_store: Optional[dict] = None):
        self.ks = killswitch or KillSwitch()
        self.budget = budget or AIBudget()
        self.log = decisions or DecisionLog()
        self.market = market or MarketResearch()
        self.tracker_factory = tracker_factory or (lambda: PerformanceTracker.from_supabase(days=30))
        self.notify = notify or self._default_notify
        self.state = state_store if state_store is not None else {}   # Redis لاحقًا؛ dict الآن
        self.last_tick: Optional[dict] = None

    # ── التنفيذ الحتمي لقرارات الدرجة 0/1 ─────────────────────────
    def _apply(self, d: dict) -> bool:
        a, t = d["action"], d["target"]
        if a == "exclude_symbol":
            self.state.setdefault(EXCLUDED_SYMBOLS_KEY, set()).add(t)
        elif a in ("pause_agent",):
            self.state.setdefault(PAUSED_AGENTS_KEY, set()).add(t)
        elif a == "halve_size":
            self.state[SIZE_MULT_KEY] = min(self.state.get(SIZE_MULT_KEY, 1.0), 0.5)
        elif a in ("observe", "keep", "widen_tp_review"):
            pass  # تسجيل فقط
        else:
            return False
        return True

    # ── النبضة ────────────────────────────────────────────────────────
    async def tick(self) -> dict:
        ts = datetime.now(timezone.utc).isoformat()
        if self.ks.is_stopped():
            self.last_tick = {"ts": ts, "skipped": True, "reason": self.ks.state().get("reason")}
            logger.warning("⏸️ tick skipped: kill switch ON")
            return self.last_tick

        brief = await self.market.brief()
        if brief.get("data_ok"):
            self.state[SIZE_MULT_KEY] = brief["posture"]["size_multiplier"]

        try:
            report = self.tracker_factory().report()
        except Exception as ex:  # noqa: BLE001
            logger.warning(f"performance report unavailable: {ex}")
            report = {"overall": {"n": 0}, "recommendations": []}

        applied, notified, proposed = [], [], []
        for rec in report["recommendations"]:
            d = self.log.propose(actor="nervous.scheduler", level=rec["level"], action=rec["action"],
                                 target=rec["target"], reason=rec["why"],
                                 evidence={"overall": report["overall"], "regime": brief["btc_regime"]["regime"]})
            if rec["level"] == 2:
                proposed.append(d)
                self.notify(f"🟡 طلب موافقة #{str(d['id'])[:8]}\n{rec['action']} → {rec['target']}\n{rec['why']}\n/approve_{str(d['id'])[:8]}  /reject_{str(d['id'])[:8]}")
            elif self._apply(d):
                self.log.mark_executed(d["id"]); applied.append(d)
                if rec["level"] == 1:
                    notified.append(d)
                    self.notify(f"🔵 نُفِّذ (درجة 1) #{str(d['id'])[:8]}\n{rec['action']} → {rec['target']}\n{rec['why']}\nللتراجع خلال 24 ساعة: /revert_{str(d['id'])[:8]}")

        expired = self.log.expire_stale()
        b = self.budget.status()
        if b["warn"] and not self.state.get("budget_warned"):
            self.notify(f"⚠️ إنفاق الـ AI {b['spent_usd']}$ من {b['cap_usd']}$ ({int(b['ratio']*100)}%)")
            self.state["budget_warned"] = True

        self.last_tick = {"ts": ts, "regime": brief["btc_regime"]["regime"], "data_ok": brief.get("data_ok"),
                          "closed_trades": report["overall"].get("n", 0),
                          "applied": len(applied), "notified": len(notified), "proposed": len(proposed),
                          "expired": expired, "size_multiplier": self.state.get(SIZE_MULT_KEY, 1.0),
                          "budget": b}
        logger.info(f"🧠 tick {json.dumps(self.last_tick, ensure_ascii=False)}")
        return self.last_tick

    def daily_summary(self) -> str:
        t = self.last_tick or {}
        return (f"🗓️ ملخص اليوم\nنظام BTC: {t.get('regime','?')} · صفقات مغلقة (30 يومًا): {t.get('closed_trades',0)}\n"
                f"رموز مستبعدة: {len(self.state.get(EXCLUDED_SYMBOLS_KEY, []))} · وكلاء موقوفون: {len(self.state.get(PAUSED_AGENTS_KEY, []))}\n"
                f"مضاعف الحجم: {t.get('size_multiplier',1.0)} · إنفاق AI: {t.get('budget',{}).get('spent_usd',0)}$ / {t.get('budget',{}).get('cap_usd','?')}$\n"
                f"بانتظار موافقتك: {len(self.log.pending())}")

    # ── الحلقة ────────────────────────────────────────────────────────
    async def run_forever(self, interval_s: int = 3600):
        from core.observability import init_sentry, brain_checkin
        init_sentry("brain")
        logger.info("🧠 nervous brain started")
        last_daily = last_weekly = None
        while True:
            try:
                brain_checkin("in_progress")
                await self.tick()
                brain_checkin("ok")
                now = datetime.now(timezone.utc)
                if now.hour == 6 and last_daily != now.date():
                    self.notify(self.daily_summary()); last_daily = now.date()
                if now.weekday() == 4 and now.hour == 12 and last_weekly != now.date():
                    self.notify("📊 تقرير الجمعة\n" + self.daily_summary()); last_weekly = now.date()
            except Exception as ex:  # noqa: BLE001
                brain_checkin("error")
                logger.exception(f"tick failed: {ex}")
            await asyncio.sleep(interval_s)

    @staticmethod
    def _default_notify(text: str):
        chat = os.getenv("TELEGRAM_ADMIN_CHAT_ID")
        if not chat:
            logger.info(f"[notify] {text}"); return
        try:
            from telegram_bot import send
            asyncio.get_event_loop().create_task(send(int(chat), text))
        except Exception as ex:  # noqa: BLE001
            logger.warning(f"notify failed: {ex}")


if __name__ == "__main__":
    asyncio.run(Brain().run_forever(int(os.getenv("NERVOUS_TICK_SECONDS", "3600"))))
