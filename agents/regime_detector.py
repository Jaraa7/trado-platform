"""Regime Detector - TRADO | Model: DeepSeek V4"""
import ccxt.async_support as ccxt

class RegimeDetector:
    def __init__(self, config):
        self.binance = ccxt.binance({"enableRateLimit": True})

    async def detect(self):
        try:
            ticker = await self.binance.fetch_ticker("BTC/USDT")
            ohlcv = await self.binance.fetch_ohlcv("BTC/USDT", "1d", limit=20)
            closes = [c[4] for c in ohlcv]
            ema20 = sum(closes[-20:])/20
            ema7  = sum(closes[-7:])/7
            price = closes[-1]
            change_24h = ticker.get("percentage", 0)
            if price > ema20 and ema7 > ema20: regime = "bull"
            elif price < ema20 and ema7 < ema20: regime = "bear"
            elif abs(change_24h) < 1.5: regime = "sideways"
            else: regime = "volatile"
            return {
                "regime": regime,
                "btc_price": price,
                "ema20": round(ema20, 2),
                "change_24h": round(change_24h, 2),
                "strategy_recommendation": "momentum" if regime in ("bull","volatile") else "grid" if regime == "sideways" else "swing"
            }
        except Exception as e:
            return {"regime": "unknown", "error": str(e)}

    async def close(self):
        await self.binance.close()