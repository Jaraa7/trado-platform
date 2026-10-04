"""
nervous/decisions.py — سجل القرارات (الذاكرة) وتدفق الصلاحيات 0/1/2.

propose(): يسجّل القرار قبل أي تنفيذ.
  level 0 → status=executed فورًا (المنفّذ يستدعي mark_executed بعد التنفيذ)
  level 1 → executed + notify (للمالك 24 ساعة للتراجع عبر /revert)
  level 2 → proposed وينتظر /approve أو /reject؛ ينتهي بعد 48 ساعة
التخزين: Supabase (nervous_decisions) وإلا ملف JSON محلي.
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from governance.limits import LIMITS

_FILE = Path(os.getenv("NERVOUS_DECISIONS_FILE", "data/nervous_decisions.json"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DecisionLog:
    def __init__(self, use_db: Optional[bool] = None):
        self.use_db = use_db if use_db is not None else os.getenv("NERVOUS_METRICS_ENABLED", "").lower() in ("1", "true")
        self._rows: list[dict] = []
        if not self.use_db and _FILE.exists():
            self._rows = json.loads(_FILE.read_text(encoding="utf-8"))

    # ── التخزين ──────────────────────────────────────────────────────
    def _save_local(self):
        _FILE.parent.mkdir(parents=True, exist_ok=True)
        _FILE.write_text(json.dumps(self._rows, ensure_ascii=False, indent=1), encoding="utf-8")

    def _insert(self, row: dict) -> dict:
        if self.use_db:
            from db.client import get_supabase
            res = get_supabase(service_role=True).table("nervous_decisions").insert(row).execute()
            return res.data[0] if res.data else row
        row.setdefault("id", str(uuid.uuid4()))
        self._rows.append(row); self._save_local()
        return row

    def _update(self, decision_id: str, **fields) -> dict:
        if self.use_db:
            from db.client import get_supabase
            res = (get_supabase(service_role=True).table("nervous_decisions")
                   .update(fields).eq("id", decision_id).execute())
            return res.data[0] if res.data else {"id": decision_id, **fields}
        for r in self._rows:
            if r["id"] == decision_id:
                r.update(fields); self._save_local(); return r
        raise KeyError(decision_id)

    def get(self, decision_id: str) -> Optional[dict]:
        if self.use_db:
            from db.client import get_supabase
            res = get_supabase(service_role=True).table("nervous_decisions").select("*").eq("id", decision_id).execute()
            return res.data[0] if res.data else None
        return next((r for r in self._rows if r["id"] == decision_id or r["id"].startswith(decision_id)), None)

    def pending(self) -> list[dict]:
        if self.use_db:
            from db.client import get_supabase
            return (get_supabase(service_role=True).table("nervous_decisions").select("*")
                    .eq("status", "proposed").execute().data or [])
        return [r for r in self._rows if r["status"] == "proposed"]

    # ── التدفق ───────────────────────────────────────────────────────
    def propose(self, actor: str, level: int, action: str, target: str, reason: str, evidence: dict) -> dict:
        assert level in (0, 1, 2), "level must be 0/1/2"
        row = {"actor": actor, "level": level, "action": action, "target": target,
               "reason": reason, "evidence": evidence, "created_at": _now(),
               "status": "proposed" if level == 2 else "approved"}
        return self._insert(row)

    def mark_executed(self, decision_id: str) -> dict:
        return self._update(decision_id, status="executed", executed_at=_now())

    def approve(self, decision_id: str, by: str) -> dict:
        d = self.get(decision_id)
        if not d or d["status"] != "proposed":
            raise ValueError("القرار غير موجود أو ليس بانتظار موافقة")
        return self._update(d["id"], status="approved", approved_by=by)

    def reject(self, decision_id: str, by: str) -> dict:
        d = self.get(decision_id)
        if not d or d["status"] not in ("proposed", "approved"):
            raise ValueError("القرار غير موجود أو لا يمكن رفضه")
        return self._update(d["id"], status="rejected", approved_by=by)

    def revert(self, decision_id: str, by: str) -> dict:
        d = self.get(decision_id)
        if not d or d["status"] != "executed":
            raise ValueError("لا يمكن التراجع إلا عن قرار منفَّذ")
        return self._update(d["id"], status="reverted", approved_by=by)

    def expire_stale(self) -> int:
        """قرارات الدرجة 2 التي تجاوزت مهلة الانتظار → expired."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=LIMITS.level2_expiry_hours)
        n = 0
        for d in self.pending():
            if datetime.fromisoformat(d["created_at"]) < cutoff:
                self._update(d["id"], status="expired"); n += 1
        return n

    def record_outcome(self, decision_id: str, horizon: str, outcome: dict) -> dict:
        assert horizon in ("24h", "7d")
        return self._update(decision_id, **{f"outcome_{horizon}": outcome})
