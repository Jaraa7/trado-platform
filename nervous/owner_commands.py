"""
nervous/owner_commands.py — أوامر المالك في تيليجرام.

تُقبل فقط من TELEGRAM_ADMIN_CHAT_ID. أي chat آخر يُتجاهل بصمت (لا نكشف وجود الأوامر).
  /stop <سبب>      إيقاف كل تنفيذ ونشر فورًا
  /resume          استئناف
  /status          حالة النظام والميزانية وقرارات بانتظارك
  /pending         قائمة قرارات الدرجة 2
  /approve_<id>    موافقة   /reject_<id>  رفض   /revert_<id>  تراجع عن قرار درجة 1
"""
from __future__ import annotations

import os
from typing import Optional

from governance.killswitch import KillSwitch
from governance.budget import AIBudget
from nervous.decisions import DecisionLog


def is_owner(chat_id: int) -> bool:
    admin = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")
    return bool(admin) and str(chat_id) == str(admin)


class OwnerCommands:
    def __init__(self, ks: Optional[KillSwitch] = None, log: Optional[DecisionLog] = None,
                 budget: Optional[AIBudget] = None):
        self.ks = ks or KillSwitch()
        self.log = log or DecisionLog()
        self.budget = budget or AIBudget()

    def handle(self, chat_id: int, text: str) -> Optional[str]:
        """يرجع نص الرد، أو None إذا لم يكن أمر مالك (أو المرسل ليس المالك)."""
        if not is_owner(chat_id) or not text.startswith("/"):
            return None
        cmd, _, arg = text.strip().partition(" ")
        cmd = cmd.split("@")[0]

        if cmd == "/stop":
            st = self.ks.stop(arg or "manual", by=f"owner:{chat_id}")
            return f"🛑 تم الإيقاف. السبب: {st['reason']}\nلا تنفيذ ولا نشر حتى /resume"
        if cmd == "/resume":
            self.ks.resume(by=f"owner:{chat_id}")
            return "▶️ تم الاستئناف."
        if cmd == "/status":
            ks = self.ks.state(); b = self.budget.status(); p = self.log.pending()
            return (f"{'🛑 موقوف' if ks.get('stopped') else '🟢 يعمل'}"
                    f"{' — ' + str(ks.get('reason')) if ks.get('stopped') else ''}\n"
                    f"إنفاق AI: {b['spent_usd']}$ / {b['cap_usd']}$\n"
                    f"بانتظار موافقتك: {len(p)}" + ("\n/pending للقائمة" if p else ""))
        if cmd == "/pending":
            p = self.log.pending()
            if not p:
                return "لا قرارات معلّقة."
            return "\n\n".join(f"#{str(d['id'])[:8]} {d['action']} → {d['target']}\n{d['reason']}\n"
                               f"/approve_{str(d['id'])[:8]}  /reject_{str(d['id'])[:8]}" for d in p)
        for verb, fn, ok in (("approve", self.log.approve, "✅ تمت الموافقة"),
                             ("reject", self.log.reject, "❌ تم الرفض"),
                             ("revert", self.log.revert, "↩️ تم التراجع")):
            if cmd.startswith(f"/{verb}_"):
                did = cmd[len(verb) + 2:]
                try:
                    d = fn(did, by=f"owner:{chat_id}")
                    return f"{ok} #{str(d['id'])[:8]} ({d['action']} → {d['target']})"
                except (ValueError, KeyError) as ex:
                    return f"⚠️ {ex}"
        return None
