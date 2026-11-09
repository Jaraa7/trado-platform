"""Persistence. InMemoryStore for tests/sim; SupabaseStore (service role) for production."""
from __future__ import annotations
import os
from datetime import datetime, timezone
from typing import List


def _iso(ms: int | None):
    return None if not ms else datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()


class InMemoryStore:
    def __init__(self):
        self.managers, self.trades, self.deaths, self.lessons, self.treasury = {}, [], [], [], []
        self.reviews, self.llm_costs = [], []
        self._n = 0

    NOT_NULL = ("family", "variant", "generation", "status", "stage", "genome", "universe", "balance")

    def create_manager(self, row: dict) -> int:
        # mimic the DB: explicit NULL in a NOT NULL column is an error (born_at has a default, so must be absent)
        assert row.get("born_at", "absent") != None, "born_at=None would violate NOT NULL"  # noqa: E711
        assert all(row.get(k) is not None for k in self.NOT_NULL if k in row)
        self._n += 1
        self.managers[self._n] = dict(row, id=self._n)
        return self._n

    def update_managers(self, rows: List[dict]):
        for r in rows:
            self.managers[r["id"]].update(r)

    def insert_trades(self, rows: List[dict]):
        self.trades.extend(rows)

    def save_death(self, row: dict):
        self.deaths.append(row)

    def save_lesson(self, row: dict):
        self.lessons.append(row)

    def load_active_lessons(self) -> List[dict]:
        return [l for l in self.lessons if l.get("active")]

    def save_treasury(self, row: dict):
        self.treasury.append(row)

    def load_alive(self) -> List[dict]:
        return [r for r in self.managers.values() if r["status"] != "dead"]

    def last_treasury(self):
        return self.treasury[-1] if self.treasury else None

    def save_review(self, row: dict):
        self.reviews.append(row)

    def add_llm_cost(self, row: dict):
        self.llm_costs.append(dict(row, ts=datetime.now(timezone.utc).isoformat()))

    def month_llm_cost(self, ym: str) -> float:
        return sum(float(r["cost_usd"]) for r in self.llm_costs if r["ts"].startswith(ym))


class SupabaseStore:
    """Uses the existing supabase client. Needs SUPABASE_URL + SUPABASE_SERVICE_KEY."""

    def __init__(self, arena: str = "main"):
        from supabase import create_client
        self.arena = arena
        url, key = os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"]
        self.sb = create_client(url, key)

    def create_manager(self, row: dict) -> int:
        r = {k: v for k, v in row.items() if k != "id"}
        if self.arena != "main":
            r["arena"] = self.arena
        return self.sb.table("t100_managers").insert(r).execute().data[0]["id"]

    def update_managers(self, rows: List[dict]):
        if rows:
            self.sb.table("t100_managers").upsert(rows).execute()

    def insert_trades(self, rows: List[dict]):
        if rows:
            self.sb.table("t100_trades").insert(rows).execute()

    def save_death(self, row: dict):
        self.sb.table("t100_deaths").insert(row).execute()

    def save_lesson(self, row: dict):
        self.sb.table("t100_lessons").insert(row).execute()

    def load_active_lessons(self) -> List[dict]:
        return (self.sb.table("t100_lessons").select("family,lesson").eq("active", True)
                .is_("retired_at", "null").execute().data)

    def save_treasury(self, row: dict):
        if self.arena != "main":
            row = dict(row, arena=self.arena)
        self.sb.table("t100_treasury").insert(row).execute()

    def last_treasury(self):
        q = self.sb.table("t100_treasury").select("*").eq("arena", self.arena)
        d = q.order("ts", desc=True).limit(1).execute().data
        return d[0] if d else None

    def save_review(self, row: dict):
        self.sb.table("t100_reviews").insert(row).execute()

    def add_llm_cost(self, row: dict):
        self.sb.table("t100_llm_costs").insert(row).execute()

    def month_llm_cost(self, ym: str) -> float:
        y, m = map(int, ym.split("-"))
        nxt = f"{y + (m == 12)}-{(m % 12) + 1:02d}-01"
        rows = (self.sb.table("t100_llm_costs").select("cost_usd").gte("ts", f"{ym}-01")
                .lt("ts", nxt).execute().data)
        return sum(float(r["cost_usd"]) for r in rows)

    def load_alive(self) -> List[dict]:
        out, start = [], 0
        while True:
            page = (self.sb.table("t100_managers").select("*").neq("status", "dead")
                    .eq("arena", self.arena).range(start, start + 999).execute().data)
            out += page
            if len(page) < 1000:
                return out
            start += 1000


def trade_row(manager_id: int, t: dict, mode: str = "paper") -> dict:
    return {"manager_id": manager_id, "symbol": t["symbol"], "side": t["side"], "mode": mode,
            "leverage": t["leverage"], "entry_price": t["entry_price"], "exit_price": t["exit_price"],
            "qty": t["qty"], "stop_price": t["stop_price"], "target_price": t["target_price"],
            "fees": round(t["fees"], 6), "pnl": round(t["pnl"], 6), "reason_in": t["reason_in"],
            "reason_out": t["reason_out"], "opened_at": _iso(t["opened_ts"]), "closed_at": _iso(t["closed_ts"])}
