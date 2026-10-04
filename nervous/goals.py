"""
nervous/goals.py — محرك ترتيب الأهداف: الأهم ← المهم ← لاحقًا.

الطريقة: درجة WSJF معدّلة (Weighted Shortest Job First):
    score = (impact*0.45 + urgency*0.35 + confidence*0.20) / effort
كل معامل من 1 إلى 10. الأثر = كم يحرّك أحد المقاييس الحاكمة الثلاثة
(ربح/مشترك، احتفاظ، أخطاء إنتاج). الاستعجال = كلفة التأخير.
الثقة = ثقتك في أن التنفيذ يحقق الأثر. الجهد = أيام العمل تقريبًا.

التبعيات تُحترم: هدف لا يُرتَّب قبل ما يعتمد عليه مهما ارتفعت درجته.
التخزين: ملف JSON محلي افتراضيًا، وSupabase (جدول nervous_goals) إن توفر.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

TIER_TOP = "الأهم"
TIER_IMPORTANT = "المهم"
TIER_LATER = "لاحقًا"

_WEIGHTS = {"impact": 0.45, "urgency": 0.35, "confidence": 0.20}


def _clamp(v: float, lo: float = 1, hi: float = 10) -> float:
    return max(lo, min(hi, float(v)))


@dataclass
class Goal:
    id: str
    title: str
    impact: float            # 1-10 كم يحرك المقاييس الحاكمة
    urgency: float           # 1-10 كلفة التأخير
    effort: float            # 1-10 أيام عمل تقريبًا
    confidence: float = 7    # 1-10 ثقة أن التنفيذ يحقق الأثر
    metric: str = ""         # profit_per_user | retention | prod_errors | other
    depends_on: list[str] = field(default_factory=list)
    status: str = "open"     # open | doing | done | dropped
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        self.impact = _clamp(self.impact)
        self.urgency = _clamp(self.urgency)
        self.effort = _clamp(self.effort)
        self.confidence = _clamp(self.confidence)
        if self.id in self.depends_on:
            raise ValueError(f"الهدف {self.id} لا يمكن أن يعتمد على نفسه")

    @property
    def score(self) -> float:
        num = (self.impact * _WEIGHTS["impact"]
               + self.urgency * _WEIGHTS["urgency"]
               + self.confidence * _WEIGHTS["confidence"])
        return round(num / self.effort, 3)


class GoalEngine:
    def __init__(self, store_path: Optional[str] = None):
        self.store_path = Path(store_path or os.getenv("NERVOUS_GOALS_PATH", "data/nervous_goals.json"))
        self._goals: dict[str, Goal] = {}
        self._load()

    # ── التخزين ──────────────────────────────────────────────────────
    def _load(self):
        if self.store_path.exists():
            raw = json.loads(self.store_path.read_text(encoding="utf-8"))
            self._goals = {g["id"]: Goal(**g) for g in raw}

    def save(self):
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.store_path.write_text(
            json.dumps([asdict(g) for g in self._goals.values()], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ── CRUD ─────────────────────────────────────────────────────────
    def add(self, goal: Goal) -> Goal:
        if goal.id in self._goals:
            raise ValueError(f"الهدف {goal.id} موجود مسبقًا")
        for dep in goal.depends_on:
            if dep not in self._goals:
                raise ValueError(f"التبعية {dep} غير موجودة")
        self._goals[goal.id] = goal
        self._assert_no_cycle()
        return goal

    def update(self, goal_id: str, **fields) -> Goal:
        g = self.get(goal_id)
        data = asdict(g)
        data.update(fields)
        self._goals[goal_id] = Goal(**data)
        self._assert_no_cycle()
        return self._goals[goal_id]

    def get(self, goal_id: str) -> Goal:
        if goal_id not in self._goals:
            raise KeyError(f"لا يوجد هدف بالمعرف {goal_id}")
        return self._goals[goal_id]

    def all(self) -> list[Goal]:
        return list(self._goals.values())

    # ── الترتيب ──────────────────────────────────────────────────────
    def _assert_no_cycle(self):
        seen, stack = set(), set()

        def visit(gid):
            if gid in stack:
                raise ValueError(f"تبعية دائرية عند {gid}")
            if gid in seen:
                return
            stack.add(gid)
            for d in self._goals[gid].depends_on:
                if d in self._goals:
                    visit(d)
            stack.remove(gid)
            seen.add(gid)

        for gid in self._goals:
            visit(gid)

    def ranked(self, include_done: bool = False) -> list[Goal]:
        """ترتيب نهائي: الدرجة الأعلى أولًا، مع احترام التبعيات."""
        candidates = {g.id: g for g in self._goals.values()
                      if include_done or g.status in ("open", "doing")}
        done_ids = {g.id for g in self._goals.values() if g.status == "done"}
        ordered: list[Goal] = []
        placed: set[str] = set(done_ids)
        remaining = dict(candidates)
        while remaining:
            ready = [g for g in remaining.values()
                     if all(d in placed or d not in self._goals for d in g.depends_on)]
            if not ready:  # تبعيات معلّقة على أهداف مسقطة → اعتبرها جاهزة
                ready = list(remaining.values())
            best = max(ready, key=lambda g: (g.score, -g.effort))
            ordered.append(best)
            placed.add(best.id)
            del remaining[best.id]
        return ordered

    def tiers(self) -> dict[str, list[Goal]]:
        """الأهم = أعلى 20% (على الأقل واحد)، المهم = التالي 30%، الباقي لاحقًا."""
        r = self.ranked()
        n = len(r)
        if n == 0:
            return {TIER_TOP: [], TIER_IMPORTANT: [], TIER_LATER: []}
        top_n = max(1, round(n * 0.2))
        imp_n = max(0, round(n * 0.3))
        return {
            TIER_TOP: r[:top_n],
            TIER_IMPORTANT: r[top_n:top_n + imp_n],
            TIER_LATER: r[top_n + imp_n:],
        }

    def next_action(self) -> Optional[Goal]:
        r = self.ranked()
        return r[0] if r else None

    def report(self) -> str:
        lines = []
        for tier, goals in self.tiers().items():
            lines.append(f"\n## {tier}")
            for g in goals:
                deps = f" (بعد: {', '.join(g.depends_on)})" if g.depends_on else ""
                lines.append(f"- [{g.score:>5}] {g.title}{deps} — {g.status}")
        return "\n".join(lines).strip()
