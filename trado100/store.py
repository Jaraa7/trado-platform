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
        self._n = 0

    def create_manager(self, row: dict) -> int:
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

    def save_treasury(self, row: dict):
        self.treasury.append(row)

    def load_alive(self) -> List[dict]:
        return [r for r in self.managers.values() if r["status"] != "dead"]

    def last_treasury(self):
        return self.treasury[-1] if self.treasury else None


class SupabaseStore:
    """Uses the existing supabase client. Needs SUPABASE_URL + SUPABASE_SERVICE_KEY."""

    def __init__(self):
        from supabase import create_client
        url, key = os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"]
        self.sb = create_client(url, key)

    def create_manager(self, row: dict) -> int:
        r = {k: v for k, v in row.items() if k != "id"}
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

    def save_treasury(self, row: dict):
        self.sb.table("t100_treasury").insert(row).execute()

    def last_treasury(self):
        d = self.sb.table("t100_treasury").select("*").order("ts", desc=True).limit(1).execute().data
        return d[0] if d else None

    def load_alive(self) -> List[dict]:
        out, start = [], 0
        while True:
            page = (self.sb.table("t100_managers").select("*").neq("status", "dead")
                    .range(start, start + 999).execute().data)
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
