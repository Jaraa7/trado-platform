"""Bybit v5 public REST (no keys needed): universe, closed 15m klines, funding, sentiment."""
from __future__ import annotations
import time
from typing import Dict, List, Optional
import httpx
import numpy as np

BASE = "https://api.bybit.com"
BAR_MS = 900_000


# Equity / commodity / FX perps follow market hours and gap; keep the arena crypto-only.
NON_CRYPTO = {"XAU", "XAG", "XPT", "XPD", "TSLA", "NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "GOOG", "META",
              "COIN", "MSTR", "HOOD", "CRCL", "PLTR", "AMD", "NFLX", "SPY", "QQQ", "EUR", "GBP", "JPY",
              "OIL", "WTI", "BRENT", "NG", "COPPER"}


class Feed:
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self.c = client or httpx.AsyncClient(timeout=15, headers={"User-Agent": "trado-100"})

    async def _get(self, path: str, **params):
        for attempt in range(3):
            try:
                r = await self.c.get(BASE + path, params=params)
                r.raise_for_status()
                j = r.json()
                if j.get("retCode") == 0:
                    return j["result"]
            except httpx.HTTPError:
                pass
            time.sleep(0.5 * (attempt + 1))
        return None

    async def universe(self, top: int = 50) -> Dict[str, float]:
        """Top USDT linear perps by 24h turnover -> {symbol: funding_rate}."""
        res = await self._get("/v5/market/tickers", category="linear")
        if not res:
            return {}
        rows = [t for t in res["list"] if t["symbol"].endswith("USDT") and "-" not in t["symbol"]
                and t["symbol"][:-4] not in NON_CRYPTO]
        rows.sort(key=lambda t: float(t.get("turnover24h") or 0), reverse=True)
        return {t["symbol"]: float(t.get("fundingRate") or 0) for t in rows[:top]}

    async def klines(self, symbol: str, bars: int = 1000, end_ms: Optional[int] = None) -> np.ndarray:
        """Closed 15m bars, oldest first. Pages backwards in blocks of 1000."""
        now = int(time.time() * 1000)
        end = end_ms or now
        out: List[list] = []
        while len(out) < bars:
            res = await self._get("/v5/market/kline", category="linear", symbol=symbol,
                                  interval="15", limit=min(1000, bars - len(out)), end=end)
            if not res or not res["list"]:
                break
            page = res["list"]                       # newest first
            out += page
            end = int(page[-1][0]) - 1
            if len(page) < 2:
                break
        if not out:
            return np.empty((0, 6))
        a = np.array([[float(x) for x in r[:6]] for r in out])[::-1]   # ts,o,h,l,c,v oldest->newest
        a = a[a[:, 0] + BAR_MS <= now]                                 # keep CLOSED bars only
        _, idx = np.unique(a[:, 0], return_index=True)
        return a[idx]

    async def funding_history(self, symbol: str, limit: int = 200) -> np.ndarray:
        """[[ts_ms, rate]] oldest first (8h settlements)."""
        res = await self._get("/v5/market/funding/history", category="linear", symbol=symbol, limit=limit)
        if not res or not res["list"]:
            return np.empty((0, 2))
        return np.array([[float(r["fundingRateTimestamp"]), float(r["fundingRate"])] for r in res["list"]])[::-1]

    async def sentiment_history(self, days: int = 90) -> np.ndarray:
        """[[ts_ms, -1..1]] oldest first (daily Fear & Greed)."""
        try:
            r = await self.c.get("https://api.alternative.me/fng/", params={"limit": days})
            rows = [[float(d["timestamp"]) * 1000, (float(d["value"]) - 50) / 50] for d in r.json()["data"]]
            return np.array(rows)[::-1]
        except Exception:
            return np.empty((0, 2))

    async def sentiment(self) -> Optional[float]:
        """Fear & Greed 0..100 -> -1 (extreme fear) .. +1 (extreme greed)."""
        try:
            r = await self.c.get("https://api.alternative.me/fng/", params={"limit": 1})
            return (float(r.json()["data"][0]["value"]) - 50) / 50
        except Exception:
            return None
