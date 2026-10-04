"""
nervous/market.py — أداة دراسة السوق الحتمية.

تستهلك data_sources الموجودة (PriceSource, OHLCVSource, SentimentSource)
ولا تكرر أي استدعاء API؛ تضيف فقط الحساب الذي كان ناقصًا:
نظام السوق (regime)، التقلب، قوة الاتجاه، أفضل/أسوأ المحركات، واتساع السوق.

كل دوال الحساب نقية (تأخذ شموعًا وترجع أرقامًا) لتُختبر بلا شبكة.
المخرج النهائي `brief()` هو ما يقرأه regime_detector وmarket_researcher.
"""
from __future__ import annotations

import asyncio
import math
from datetime import datetime, timezone
from typing import Iterable

DEFAULT_UNIVERSE = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT",
                    "ADA/USDT", "DOGE/USDT", "AVAX/USDT", "LINK/USDT", "DOT/USDT"]


# ── حسابات نقية ────────────────────────────────────────────────────────
def ema(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    k = 2 / (period + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def atr(candles: list[dict], period: int = 14) -> float:
    if len(candles) < 2:
        return 0.0
    trs = []
    for prev, cur in zip(candles[:-1], candles[1:]):
        trs.append(max(cur["high"] - cur["low"],
                       abs(cur["high"] - prev["close"]),
                       abs(cur["low"] - prev["close"])))
    window = trs[-period:]
    return sum(window) / len(window) if window else 0.0


def adx(candles: list[dict], period: int = 14) -> float:
    """قوة الاتجاه 0-100 (Wilder). يحتاج 2*period شمعة على الأقل."""
    n = len(candles)
    if n < period * 2:
        return 0.0
    plus_dm, minus_dm, tr = [], [], []
    for prev, cur in zip(candles[:-1], candles[1:]):
        up, down = cur["high"] - prev["high"], prev["low"] - cur["low"]
        plus_dm.append(up if up > down and up > 0 else 0.0)
        minus_dm.append(down if down > up and down > 0 else 0.0)
        tr.append(max(cur["high"] - cur["low"], abs(cur["high"] - prev["close"]), abs(cur["low"] - prev["close"])))

    def smooth(xs):
        s = [sum(xs[:period])]
        for x in xs[period:]:
            s.append(s[-1] - s[-1] / period + x)
        return s

    tr_s, p_s, m_s = smooth(tr), smooth(plus_dm), smooth(minus_dm)
    dx = []
    for t, p, m in zip(tr_s, p_s, m_s):
        if t == 0:
            dx.append(0.0); continue
        pdi, mdi = 100 * p / t, 100 * m / t
        dx.append(0.0 if pdi + mdi == 0 else 100 * abs(pdi - mdi) / (pdi + mdi))
    if len(dx) < period:
        return round(sum(dx) / len(dx), 2) if dx else 0.0
    a = sum(dx[:period]) / period
    for d in dx[period:]:
        a = (a * (period - 1) + d) / period
    return round(a, 2)


def realized_volatility(candles: list[dict], window: int = 24) -> float:
    """تقلب محقق % على نافذة الشموع (انحراف معياري للعوائد اللوغاريتمية)."""
    closes = [c["close"] for c in candles[-(window + 1):] if c["close"] > 0]
    if len(closes) < 3:
        return 0.0
    rets = [math.log(b / a) for a, b in zip(closes[:-1], closes[1:])]
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    return round(math.sqrt(var) * 100, 3)


def classify_regime(candles: list[dict]) -> dict:
    """
    يصنّف السوق إلى: trending_up / trending_down / ranging / volatile.
    القاعدة: ADX>25 اتجاه (اتجاهه من EMA20 مقابل EMA50)، وإلا نطاق؛
    وإذا ATR/السعر > 4% فهو متقلب مهما كان الاتجاه.
    """
    if len(candles) < 60:
        return {"regime": "unknown", "adx": 0, "atr_pct": 0, "ema_bias": "flat", "reason": "شموع غير كافية"}
    closes = [c["close"] for c in candles]
    e20, e50 = ema(closes, 20)[-1], ema(closes, 50)[-1]
    price = closes[-1]
    a = adx(candles)
    atr_pct = round(100 * atr(candles) / price, 3) if price else 0
    bias = "up" if e20 > e50 * 1.002 else "down" if e20 < e50 * 0.998 else "flat"
    if atr_pct > 4:
        regime = "volatile"
    elif a > 25 and bias == "up":
        regime = "trending_up"
    elif a > 25 and bias == "down":
        regime = "trending_down"
    else:
        regime = "ranging"
    return {"regime": regime, "adx": a, "atr_pct": atr_pct, "ema_bias": bias,
            "reason": f"ADX={a}, ATR%={atr_pct}, EMA20 {bias} EMA50"}


def rank_movers(tickers: Iterable[dict], top: int = 3) -> dict:
    rows = [t for t in tickers if t.get("price")]
    by_change = sorted(rows, key=lambda t: t.get("change_24h", 0), reverse=True)
    return {
        "gainers": [{"symbol": t["symbol"], "change_24h": round(t["change_24h"], 2)} for t in by_change[:top]],
        "losers":  [{"symbol": t["symbol"], "change_24h": round(t["change_24h"], 2)} for t in by_change[-top:][::-1]],
        "breadth_pct_up": round(100 * sum(1 for t in rows if t.get("change_24h", 0) > 0) / len(rows), 1) if rows else 0,
    }


def recommend_posture(btc_regime: dict, fear_greed: int, breadth_up: float) -> dict:
    """
    توصية حتمية لوضعية الاستراتيجيات (لـ paper trading):
    - trending + breadth واسع → ترجيح استراتيجيات الاتجاه
    - ranging → ترجيح mean reversion وتقليل الرافعة
    - volatile أو خوف شديد → تقليص الحجم للنصف
    """
    r = btc_regime.get("regime", "unknown")
    size = 1.0
    favor = []
    if r in ("trending_up", "trending_down") and breadth_up > 60:
        favor = ["trend_following", "breakout"]
    elif r == "ranging":
        favor = ["mean_reversion", "range_scalp"]
    elif r == "volatile":
        favor = ["mean_reversion"]; size = 0.5
    if fear_greed <= 20 or fear_greed >= 80:
        size = min(size, 0.5)
    return {"favor": favor, "size_multiplier": size,
            "note": f"نظام BTC={r}, خوف/طمع={fear_greed}, اتساع={breadth_up}%"}


# ── الواجهة الشبكية ───────────────────────────────────────────────────
class MarketResearch:
    def __init__(self, universe: list[str] | None = None, exchange: str = "bybit"):
        self.universe = universe or DEFAULT_UNIVERSE
        self.exchange = exchange

    async def brief(self, interval: str = "1h") -> dict:
        from data_sources.market import PriceSource, OHLCVSource, SentimentSource

        tickers, fg, btc_candles = await asyncio.gather(
            asyncio.gather(*[PriceSource.get_price(s, self.exchange) for s in self.universe],
                           return_exceptions=True),
            SentimentSource.get_fear_greed(),
            OHLCVSource.get("BTC/USDT", interval, 200, self.exchange),
        )
        tickers = [t for t in tickers if isinstance(t, dict) and t.get("price", 0) > 0]
        movers = rank_movers(tickers)
        btc = classify_regime(btc_candles)
        fg_val = int(fg.get("value", 50))
        return {
            "ts": datetime.now(timezone.utc).isoformat(),
            "exchange": self.exchange,
            "interval": interval,
            "btc_regime": btc,
            "btc_volatility_pct": realized_volatility(btc_candles),
            "fear_greed": {"value": fg_val, "label": fg.get("label"), "trend": fg.get("trend")},
            "movers": movers,
            "posture": recommend_posture(btc, fg_val, movers["breadth_pct_up"]),
            "coverage": f"{len(tickers)}/{len(self.universe)} رموز",
            "data_ok": len(tickers) >= len(self.universe) // 2 and len(btc_candles) >= 60,
        }
