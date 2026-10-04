"""
nervous/performance.py — قياس الأداء وتحسينه (حتمي).

ما كان ناقصًا: لا شيء في المنصة يقيس ماذا حدث لإشارة بعد صدورها.
هذه الأداة:
1. evaluate_outcome(): تحدد من الشموع اللاحقة هل ضُرب TP أم SL أم انتهت الصلاحية،
   وتحسب R-multiple (الربح بوحدات المخاطرة).
2. PerformanceTracker.stats(): win rate، expectancy، profit factor،
   أقصى تراجع، لكل وكيل/رمز/استراتيجية.
3. recommendations(): قواعد صريحة تخرج إجراءات محددة مصنّفة بدرجة الصلاحية
   (0 = ينفَّذ وحده، 1 = ينفَّذ ويبلّغ، 2 = يحتاج موافقتك).

يعمل على قائمة dicts بنفس أعمدة جدول signals الموجود، أو يقرأها من Supabase.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Iterable, Optional

MIN_SAMPLE = 20  # تحت هذا العدد لا نصدر أحكامًا، فقط نراقب


# ── 1. نتيجة إشارة واحدة ─────────────────────────────────────────────
def evaluate_outcome(signal: dict, candles_after: list[dict]) -> dict:
    """
    signal: {direction: long|short, entry_price, stop_loss, take_profit_1}
    candles_after: شموع بعد وقت الإشارة بترتيب زمني.
    القاعدة المحافظة: إذا لمست شمعة واحدة TP وSL معًا نعتبرها SL.
    """
    d = (signal.get("direction") or "long").lower()
    entry = float(signal["entry_price"]); sl = float(signal["stop_loss"])
    tp = signal.get("take_profit_1")
    tp = float(tp) if tp else None
    risk = abs(entry - sl)
    if risk == 0:
        return {"status": "invalid", "r_multiple": 0.0, "bars": 0}

    for i, c in enumerate(candles_after, 1):
        hi, lo = c["high"], c["low"]
        if d == "long":
            hit_sl = lo <= sl
            hit_tp = tp is not None and hi >= tp
        else:
            hit_sl = hi >= sl
            hit_tp = tp is not None and lo <= tp
        if hit_sl:
            return {"status": "hit_sl", "r_multiple": -1.0, "bars": i}
        if hit_tp:
            return {"status": "hit_tp", "r_multiple": round(abs(tp - entry) / risk, 3), "bars": i}

    if not candles_after:
        return {"status": "active", "r_multiple": 0.0, "bars": 0}
    last = candles_after[-1]["close"]
    pnl = (last - entry) if d == "long" else (entry - last)
    return {"status": "expired", "r_multiple": round(pnl / risk, 3), "bars": len(candles_after)}


# ── 2. الإحصاءات ─────────────────────────────────────────────────────
def _max_drawdown(r_series: Iterable[float]) -> float:
    peak = equity = dd = 0.0
    for r in r_series:
        equity += r
        peak = max(peak, equity)
        dd = max(dd, peak - equity)
    return round(dd, 3)


def compute_stats(outcomes: list[dict]) -> dict:
    """outcomes: [{status, r_multiple}] للإشارات المغلقة فقط."""
    closed = [o for o in outcomes if o.get("status") in ("hit_tp", "hit_sl", "expired")]
    n = len(closed)
    if n == 0:
        return {"n": 0, "win_rate": 0, "expectancy_r": 0, "profit_factor": 0, "max_drawdown_r": 0, "total_r": 0}
    rs = [float(o["r_multiple"]) for o in closed]
    wins = [r for r in rs if r > 0]; losses = [-r for r in rs if r < 0]
    pf = (sum(wins) / sum(losses)) if losses else (float("inf") if wins else 0)
    return {
        "n": n,
        "win_rate": round(100 * len(wins) / n, 1),
        "expectancy_r": round(sum(rs) / n, 3),
        "profit_factor": round(pf, 2) if pf != float("inf") else 99.0,
        "max_drawdown_r": _max_drawdown(rs),
        "total_r": round(sum(rs), 2),
        "avg_bars": round(sum(o.get("bars", 0) for o in closed) / n, 1),
    }


class PerformanceTracker:
    def __init__(self, signals: Optional[list[dict]] = None):
        """signals: dicts بأعمدة جدول signals + status + r_multiple (إن حُسبت)."""
        self.signals = signals or []

    @classmethod
    def from_supabase(cls, days: int = 30) -> "PerformanceTracker":
        from db.client import get_supabase
        sb = get_supabase(service_role=True)
        rows = (sb.table("signals").select("*")
                .gte("created_at", f"now() - interval '{int(days)} days'")
                .execute().data or [])
        return cls(rows)

    def _outcome(self, s: dict) -> dict:
        return {"status": s.get("status", "active"), "r_multiple": float(s.get("r_multiple") or 0),
                "bars": int(s.get("bars") or 0)}

    def stats(self) -> dict:
        return compute_stats([self._outcome(s) for s in self.signals])

    def breakdown(self, key: str = "generated_by") -> dict[str, dict]:
        groups: dict[str, list] = defaultdict(list)
        for s in self.signals:
            groups[str(s.get(key) or "unknown")].append(self._outcome(s))
        return {k: compute_stats(v) for k, v in groups.items()}

    # ── 3. التوصيات ─────────────────────────────────────────────────
    def recommendations(self) -> list[dict]:
        """
        قواعد حتمية → إجراءات. كل إجراء يحمل level (0/1/2) ليدخل تدفق الصلاحيات.
        """
        recs: list[dict] = []
        overall = self.stats()
        if overall["n"] < MIN_SAMPLE:
            recs.append({"level": 0, "action": "observe",
                         "target": "all",
                         "why": f"العينة {overall['n']} إشارة فقط؛ نحتاج {MIN_SAMPLE} قبل أي حكم"})
            return recs

        for agent, st in self.breakdown("generated_by").items():
            if st["n"] < MIN_SAMPLE:
                continue
            if st["expectancy_r"] < 0 and st["profit_factor"] < 0.9:
                recs.append({"level": 1, "action": "pause_agent", "target": agent,
                             "why": f"توقّع {st['expectancy_r']}R وعامل ربح {st['profit_factor']} على {st['n']} إشارة"})
            elif st["max_drawdown_r"] > 10:
                recs.append({"level": 1, "action": "halve_size", "target": agent,
                             "why": f"تراجع أقصى {st['max_drawdown_r']}R"})
            elif st["win_rate"] < 35 and st["expectancy_r"] > 0:
                recs.append({"level": 0, "action": "widen_tp_review", "target": agent,
                             "why": f"معدل فوز {st['win_rate']}% مع توقع موجب: استراتيجية ذيل؛ راجع نسب TP/SL"})
            elif st["expectancy_r"] > 0.3 and st["profit_factor"] > 1.5:
                recs.append({"level": 2, "action": "promote_candidate", "target": agent,
                             "why": f"توقّع {st['expectancy_r']}R وعامل ربح {st['profit_factor']}: مرشح للانتقال من paper إلى live"})

        for sym, st in self.breakdown("symbol").items():
            if st["n"] >= MIN_SAMPLE and st["expectancy_r"] < -0.2:
                recs.append({"level": 0, "action": "exclude_symbol", "target": sym,
                             "why": f"توقّع {st['expectancy_r']}R على {st['n']} إشارة"})
        if not recs:
            recs.append({"level": 0, "action": "keep", "target": "all",
                         "why": f"الأداء ضمن الحدود: توقّع {overall['expectancy_r']}R، PF {overall['profit_factor']}"})
        return recs

    def report(self) -> dict:
        return {"ts": datetime.now(timezone.utc).isoformat(), "overall": self.stats(),
                "by_agent": self.breakdown("generated_by"), "by_symbol": self.breakdown("symbol"),
                "recommendations": self.recommendations()}
