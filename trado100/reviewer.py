"""Daily AI reviewer for TRADO-100.

Reads a compact snapshot of the system (deaths, diag, family stats, lessons), asks a strong LLM
to find flaws / suggest tests, stores the answer in t100_reviews and (optionally) opens GitHub
Issues. It NEVER changes trading behaviour: suggestions only, every change goes through PR + evolve.py.

Cost guard: every call is logged to t100_llm_costs; once the month's spend reaches CAP_USD the
reviewer stops and notifies once.
"""
from __future__ import annotations
import json, os, re
from datetime import datetime, timezone
from typing import Callable, Optional

from loguru import logger

CAP_USD = float(os.getenv("T100_LLM_CAP_USD", "150"))
DAILY_HOUR_UTC = 2                 # 05:00 Kuwait
MIN_GAP_H = 20                     # daily runs
DEATH_GAP_H = 6                    # extra run after deaths, at most this often
MAX_ISSUES = 3

SYSTEM = (
    "You are the code/strategy reviewer of TRADO-100, a paper-trading system of 100 algorithmic managers "
    "(10 families x 10 variants) with a hard-coded Risk Guardian and death/inheritance. "
    "You receive a JSON snapshot. Find concrete flaws: families that never trade, near-duplicate genomes, "
    "repeated death causes, suspicious results (overfitting), data/execution issues. "
    "Never propose loosening the Risk Guardian (risk<=2%, leverage<=3, DD 15% = death). "
    'Reply with ONLY JSON: {"summary": str (<=600 chars), "findings": [{"title": str, "evidence": str, '
    '"proposed_test": str, "severity": "low"|"medium"|"high"}]} with at most 5 findings.'
)


def month_key(now: datetime) -> str:
    return now.strftime("%Y-%m")


def parse_review(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no JSON in reviewer reply")
    d = json.loads(m.group(0))
    findings = [f for f in d.get("findings", []) if isinstance(f, dict) and f.get("title")][:5]
    return {"summary": str(d.get("summary", ""))[:1000], "findings": findings}


def default_llm(system: str, user: str):
    """→ (text, model, in_tok, out_tok, cost). Strong tier via the shared router."""
    from core.llm_router import LLMRouter
    r = LLMRouter().complete("frontier", system, [{"role": "user", "content": user}],
                             agent_id="t100_reviewer", max_tokens=1500)
    return r.text, r.model, r.input_tokens, r.output_tokens, r.cost_usd


def github_issue(title: str, body: str) -> Optional[str]:
    tok, repo = os.getenv("GITHUB_TOKEN"), os.getenv("GITHUB_REPO", "Jaraa7/trado-platform")
    if not tok:
        return None
    import httpx
    r = httpx.post(f"https://api.github.com/repos/{repo}/issues",
                   json={"title": title[:200], "body": body, "labels": ["t100-review"]},
                   headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"}, timeout=20)
    r.raise_for_status()
    return r.json().get("html_url")


class Reviewer:
    def __init__(self, store, llm: Callable = default_llm, issue_fn: Callable = github_issue,
                 notify: Optional[Callable[[str], None]] = None, cap: float = CAP_USD):
        self.store, self.llm, self.issue_fn, self.notify, self.cap = store, llm, issue_fn, notify, cap
        self.last_run: Optional[datetime] = None
        self.deaths_seen = 0
        self._cap_notified = None

    # ------------------------------------------------------------ scheduling
    def due(self, now: datetime, deaths_total: int) -> Optional[str]:
        gap = (now - self.last_run).total_seconds() / 3600 if self.last_run else 1e9
        if now.hour >= DAILY_HOUR_UTC and gap >= MIN_GAP_H:
            return "daily"
        if deaths_total > self.deaths_seen and gap >= DEATH_GAP_H:
            return "death"
        return None

    # ------------------------------------------------------------ run
    def run_once(self, snapshot: dict, trigger: str = "daily", now: Optional[datetime] = None) -> Optional[dict]:
        now = now or datetime.now(timezone.utc)
        spent = self.store.month_llm_cost(month_key(now))
        if spent >= self.cap:
            if self._cap_notified != month_key(now) and self.notify:
                self.notify(f"⛔ TRADO-100: LLM budget cap reached (${spent:.2f}/{self.cap:.0f}); reviewer paused until next month")
            self._cap_notified = month_key(now)
            logger.warning(f"reviewer halted: month spend {spent:.2f} >= cap {self.cap}")
            return None
        text, model, itok, otok, cost = self.llm(SYSTEM, json.dumps(snapshot, ensure_ascii=False, default=str))
        self.store.add_llm_cost({"agent": "t100_reviewer", "model": model, "input_tokens": itok,
                                 "output_tokens": otok, "cost_usd": cost})
        try:
            rev = parse_review(text)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"reviewer: unparsable reply ({e})")
            rev = {"summary": text[:600], "findings": []}
        urls = []
        for f in [f for f in rev["findings"] if f.get("severity") in ("medium", "high")][:MAX_ISSUES]:
            try:
                u = self.issue_fn(f"[t100-review] {f['title']}",
                                  f"**Evidence:** {f.get('evidence','')}\n\n**Proposed test:** {f.get('proposed_test','')}\n\n"
                                  f"_Auto-generated by the daily reviewer. Suggestion only: any change needs a PR and must pass evolve.py._")
                if u:
                    urls.append(u)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"reviewer: issue failed: {e}")
        self.store.save_review({"trigger": trigger, "model": model, "summary": rev["summary"],
                                "findings": rev["findings"], "snapshot": snapshot, "issue_urls": urls})
        self.last_run = now
        self.deaths_seen = snapshot.get("deaths_total", self.deaths_seen)
        logger.info(f"reviewer[{trigger}] done: {len(rev['findings'])} findings, ${cost:.4f}")
        return rev


def snapshot_from_arena(arena, now_ms: int) -> dict:
    live = [m for m in arena.managers.values() if m.status != "dead"]
    fam: dict = {}
    for m in live:
        f = fam.setdefault(m.family, {"n": 0, "equity": 0.0, "trades": 0, "wins": 0})
        f["n"] += 1; f["equity"] += m.equity(); f["trades"] += m.n_trades; f["wins"] += m.wins
    for f in fam.values():
        f["avg_equity"] = round(f.pop("equity") / max(f["n"], 1), 2)
        f["win_rate"] = round(f["wins"] / f["trades"], 3) if f["trades"] else None
    day = 86_400_000
    return {"alive": len(live), "vacancies": len(arena.vacancies), "kill_switch": arena.kill_switch,
            "deaths_total": len(arena.deaths_log),
            "deaths_24h": [d for d in arena.deaths_log if now_ms - d["ts"] <= day][-30:],
            "families": fam, "diag": arena.diag_summary(), "diversity": arena.diversity(),
            "lessons": [m.lessons[-1] for m in live if m.lessons][:10]}
