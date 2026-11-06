"""
📅 TradoAI — Macro Economic Calendar (free, no key)
التقويم الاقتصادي — أحداث الماكرو عالية التأثير (FOMC, CPI, NFP, ...)

Source: Forex Factory weekly public feed
  https://nfs.faireconomy.media/ff_calendar_thisweek.json
Notes:
  - Free, refreshed weekly; carries forecast + previous, NOT actual values.
  - The feed does not declare a timezone reliably; `date` is ISO-8601 with
    offset in practice. We parse it defensively and store UTC.
  - Used by Regime-Switch / Risk Guardian: block NEW entries inside a window
    around high-impact USD events (crypto reacts to USD macro).
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone

import httpx
from loguru import logger

try:  # Cache is optional during unit tests
    from cache import Cache
except Exception:  # pragma: no cover
    Cache = None

FEED_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
CACHE_TTL = 6 * 3600  # feed is weekly; 6h cache is plenty

# Events that move crypto. Everything else is noise for TRADO-100.
WATCH_CURRENCIES = {"USD"}
WATCH_KEYWORDS = (
    "fomc", "federal funds", "fed chair", "cpi", "core pce", "non-farm",
    "nonfarm", "unemployment rate", "gdp", "ppi", "retail sales", "ism",
)


@dataclass
class MacroEvent:
    title: str
    currency: str
    impact: str          # High / Medium / Low / Holiday
    time_utc: str        # ISO-8601 UTC
    forecast: str = ""
    previous: str = ""

    def dt(self) -> datetime:
        return datetime.fromisoformat(self.time_utc)


def _parse_time(raw: str) -> datetime | None:
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _is_watched(ev: dict) -> bool:
    if ev.get("currency") not in WATCH_CURRENCIES:
        return False
    if (ev.get("impact") or "").lower() == "high":
        return True
    title = (ev.get("title") or "").lower()
    return any(k in title for k in WATCH_KEYWORDS)


class MacroCalendar:
    """Weekly high-impact macro events + a trading blackout helper."""

    @staticmethod
    async def fetch(force: bool = False) -> list[MacroEvent]:
        key = "macro:calendar:week"
        if Cache and not force:
            if cached := await Cache.get(key):
                return [MacroEvent(**e) for e in cached]

        events: list[MacroEvent] = []
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(FEED_URL, headers={"User-Agent": "TradoAI/1.0"})
                r.raise_for_status()
                raw = r.json()
        except Exception as e:
            logger.warning(f"macro calendar fetch failed → {e}")
            return events

        for ev in raw if isinstance(raw, list) else []:
            if not _is_watched(ev):
                continue
            dt = _parse_time(ev.get("date", ""))
            if not dt:
                continue
            events.append(MacroEvent(
                title=ev.get("title", ""),
                currency=ev.get("currency", ""),
                impact=ev.get("impact", ""),
                time_utc=dt.isoformat(),
                forecast=str(ev.get("forecast", "") or ""),
                previous=str(ev.get("previous", "") or ""),
            ))

        events.sort(key=lambda e: e.time_utc)
        if Cache:
            await Cache.set(key, [asdict(e) for e in events], ttl=CACHE_TTL)
        logger.info(f"macro calendar: {len(events)} watched USD events this week")
        return events

    @staticmethod
    async def blackout(now: datetime | None = None,
                       before_min: int = 30,
                       after_min: int = 30) -> dict:
        """
        Is NOW inside a no-new-entries window around a high-impact event?
        Returns {"blackout": bool, "event": MacroEvent|None, "minutes_to": int|None}
        Risk Guardian calls this before approving any NEW position.
        """
        now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        events = await MacroCalendar.fetch()
        nearest, nearest_delta = None, None
        for ev in events:
            if ev.impact.lower() != "high":
                continue
            delta = (ev.dt() - now).total_seconds() / 60
            if -after_min <= delta <= before_min:
                return {"blackout": True, "event": asdict(ev),
                        "minutes_to": round(delta)}
            if delta > 0 and (nearest_delta is None or delta < nearest_delta):
                nearest, nearest_delta = ev, delta
        return {"blackout": False,
                "event": asdict(nearest) if nearest else None,
                "minutes_to": round(nearest_delta) if nearest_delta else None}

    @staticmethod
    async def upcoming(hours: int = 48) -> list[MacroEvent]:
        now = datetime.now(timezone.utc)
        horizon = now + timedelta(hours=hours)
        return [e for e in await MacroCalendar.fetch()
                if now <= e.dt() <= horizon]


if __name__ == "__main__":  # quick manual check
    async def _main():
        for e in await MacroCalendar.upcoming(24 * 7):
            print(e.time_utc, e.impact, e.title, e.forecast, e.previous)
        print(await MacroCalendar.blackout())
    asyncio.run(_main())
