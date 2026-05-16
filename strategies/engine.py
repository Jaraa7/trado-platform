"""
📈 TradoAI — Trading Strategies Engine
استراتيجيات تداول حقيقية بخوارزميات كاملة

الاستراتيجيات:
1. Trend Following   — RSI + EMA + MACD
2. Breakout Hunter   — Support/Resistance + Volume
3. Mean Reversion    — Bollinger Bands + RSI Divergence
4. Scalping Pro      — EMA Crossover + Volume Spike
5. Multi-Strategy    — يجمع كل الاستراتيجيات بنظام تصويت

كل استراتيجية تُنتج:
- direction: long | short | neutral
- entry: سعر الدخول المقترح
- stop_loss: وقف الخسارة
- take_profit: الهدف
- confidence: 0-100
- reason: تفسير القرار
"""
import numpy as np
from dataclasses import dataclass
from typing import Optional
from loguru import logger


# ─── Types ────────────────────────────────────────────────────────
@dataclass
class Signal:
    direction:   str            # long | short | neutral
    entry:       float
    stop_loss:   float
    take_profit: float
    confidence:  int            # 0-100
    risk_reward: float
    reason:      str
    indicators:  dict
    strategy:    str

    def to_dict(self):
        return {
            "direction":   self.direction,
            "entry":       round(self.entry, 6),
            "stop_loss":   round(self.stop_loss, 6),
            "take_profit": round(self.take_profit, 6),
            "confidence":  self.confidence,
            "risk_reward": round(self.risk_reward, 2),
            "reason":      self.reason,
            "indicators":  self.indicators,
            "strategy":    self.strategy,
        }


# ════════════════════════════════════════════════════════════════════
# TECHNICAL INDICATORS (حسابات حقيقية)
# ════════════════════════════════════════════════════════════════════

class Indicators:

    @staticmethod
    def ema(prices: list, period: int) -> list:
        """Exponential Moving Average"""
        k = 2 / (period + 1)
        ema = [prices[0]]
        for p in prices[1:]:
            ema.append(p * k + ema[-1] * (1 - k))
        return ema

    @staticmethod
    def sma(prices: list, period: int) -> list:
        """Simple Moving Average"""
        result = []
        for i in range(len(prices)):
            if i < period - 1:
                result.append(None)
            else:
                result.append(sum(prices[i-period+1:i+1]) / period)
        return result

    @staticmethod
    def rsi(prices: list, period: int = 14) -> list:
        """Relative Strength Index"""
        if len(prices) < period + 1:
            return [50] * len(prices)

        gains, losses = [], []
        for i in range(1, len(prices)):
            diff = prices[i] - prices[i-1]
            gains.append(max(diff, 0))
            losses.append(max(-diff, 0))

        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        rsi_vals = [50] * period  # placeholder for first period

        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period-1) + gains[i]) / period
            avg_loss = (avg_loss * (period-1) + losses[i]) / period
            if avg_loss == 0:
                rsi_vals.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi_vals.append(100 - (100 / (1 + rs)))

        return rsi_vals

    @staticmethod
    def macd(prices: list, fast: int = 12, slow: int = 26, signal: int = 9):
        """MACD + Signal + Histogram"""
        ema_fast = Indicators.ema(prices, fast)
        ema_slow = Indicators.ema(prices, slow)
        macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
        signal_line = Indicators.ema(macd_line[slow:], signal)
        # Pad signal to same length
        signal_padded = [None] * slow + signal_line
        histogram = []
        for m, s in zip(macd_line, signal_padded):
            histogram.append(m - s if s is not None else None)
        return macd_line, signal_padded, histogram

    @staticmethod
    def bollinger_bands(prices: list, period: int = 20, std_dev: float = 2.0):
        """Bollinger Bands"""
        upper, middle, lower = [], [], []
        for i in range(len(prices)):
            if i < period - 1:
                upper.append(None)
                middle.append(None)
                lower.append(None)
            else:
                window = prices[i-period+1:i+1]
                avg  = sum(window) / period
                std  = np.std(window)
                upper.append(avg + std_dev * std)
                middle.append(avg)
                lower.append(avg - std_dev * std)
        return upper, middle, lower

    @staticmethod
    def atr(highs: list, lows: list, closes: list, period: int = 14) -> list:
        """Average True Range"""
        tr_list = []
        for i in range(1, len(highs)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i]  - closes[i-1])
            )
            tr_list.append(tr)
        atr_vals = [tr_list[0]]
        for tr in tr_list[1:]:
            atr_vals.append((atr_vals[-1] * (period-1) + tr) / period)
        return [None] + atr_vals

    @staticmethod
    def support_resistance(highs: list, lows: list, lookback: int = 20) -> tuple:
        """أهم مستويات الدعم والمقاومة"""
        if len(highs) < lookback:
            return min(lows), max(highs)

        recent_highs = highs[-lookback:]
        recent_lows  = lows[-lookback:]

        # أعلى قمة في الفترة = مقاومة
        resistance = max(recent_highs)
        # أدنى قاع في الفترة = دعم
        support    = min(recent_lows)

        return support, resistance

    @staticmethod
    def volume_sma(volumes: list, period: int = 20) -> list:
        return Indicators.sma(volumes, period)

    @staticmethod
    def stochastic(highs: list, lows: list, closes: list, k_period: int = 14) -> list:
        """Stochastic Oscillator"""
        k_vals = []
        for i in range(len(closes)):
            if i < k_period - 1:
                k_vals.append(50)
            else:
                window_h = max(highs[i-k_period+1:i+1])
                window_l = min(lows[i-k_period+1:i+1])
                if window_h == window_l:
                    k_vals.append(50)
                else:
                    k = (closes[i] - window_l) / (window_h - window_l) * 100
                    k_vals.append(k)
        return k_vals


# ════════════════════════════════════════════════════════════════════
# STRATEGY 1: TREND FOLLOWING
# RSI + EMA 21/50/200 + MACD
# ════════════════════════════════════════════════════════════════════

class TrendFollowingStrategy:
    name = "Trend Following"

    @staticmethod
    def analyze(candles: list) -> Optional[Signal]:
        if len(candles) < 60:
            return None

        closes  = [c["close"]  for c in candles]
        highs   = [c["high"]   for c in candles]
        lows    = [c["low"]    for c in candles]
        volumes = [c["volume"] for c in candles]

        # Indicators
        ema21  = Indicators.ema(closes, 21)
        ema50  = Indicators.ema(closes, 50)
        rsi14  = Indicators.rsi(closes, 14)
        macd_line, signal_line, histogram = Indicators.macd(closes)
        atr14  = Indicators.atr(highs, lows, closes, 14)

        price = closes[-1]
        cur_rsi  = rsi14[-1]
        cur_ema21 = ema21[-1]
        cur_ema50 = ema50[-1]
        cur_macd  = macd_line[-1]
        cur_signal = signal_line[-1] or 0
        cur_hist  = histogram[-1] or 0
        cur_atr   = atr14[-1] or price * 0.02

        # ── LONG CONDITIONS ──────────────────────────────────────
        long_signals = 0
        long_reasons = []

        if price > cur_ema21 > cur_ema50:
            long_signals += 2
            long_reasons.append("Price above EMA21 > EMA50 (uptrend)")

        if 40 < cur_rsi < 70:
            long_signals += 1
            long_reasons.append(f"RSI {cur_rsi:.1f} in bullish zone")

        if cur_macd > cur_signal and cur_hist > 0:
            long_signals += 2
            long_reasons.append("MACD above signal, positive histogram")

        # MACD crossover (أقوى إشارة)
        prev_hist = histogram[-2] or 0
        if cur_hist > 0 and prev_hist <= 0:
            long_signals += 2
            long_reasons.append("MACD bullish crossover just occurred")

        # ── SHORT CONDITIONS ─────────────────────────────────────
        short_signals = 0
        short_reasons = []

        if price < cur_ema21 < cur_ema50:
            short_signals += 2
            short_reasons.append("Price below EMA21 < EMA50 (downtrend)")

        if cur_rsi > 65:
            short_signals += 1
            short_reasons.append(f"RSI {cur_rsi:.1f} overbought")

        if cur_macd < cur_signal and cur_hist < 0:
            short_signals += 2
            short_reasons.append("MACD below signal, negative histogram")

        if cur_hist < 0 and prev_hist >= 0:
            short_signals += 2
            short_reasons.append("MACD bearish crossover just occurred")

        # ── DECISION ─────────────────────────────────────────────
        if long_signals >= 4:
            confidence = min(95, 55 + long_signals * 6)
            entry      = price
            stop_loss  = entry - (cur_atr * 1.5)
            take_profit= entry + (cur_atr * 3.0)
            rr         = (take_profit - entry) / (entry - stop_loss)

            return Signal(
                direction="long", entry=entry,
                stop_loss=stop_loss, take_profit=take_profit,
                confidence=confidence, risk_reward=rr,
                reason=" | ".join(long_reasons),
                indicators={"rsi": round(cur_rsi,1), "ema21": round(cur_ema21,4),
                            "ema50": round(cur_ema50,4), "macd_hist": round(cur_hist,6)},
                strategy=TrendFollowingStrategy.name
            )

        if short_signals >= 4:
            confidence = min(95, 55 + short_signals * 6)
            entry      = price
            stop_loss  = entry + (cur_atr * 1.5)
            take_profit= entry - (cur_atr * 3.0)
            rr         = (entry - take_profit) / (stop_loss - entry)

            return Signal(
                direction="short", entry=entry,
                stop_loss=stop_loss, take_profit=take_profit,
                confidence=confidence, risk_reward=rr,
                reason=" | ".join(short_reasons),
                indicators={"rsi": round(cur_rsi,1), "macd_hist": round(cur_hist,6)},
                strategy=TrendFollowingStrategy.name
            )

        return None


# ════════════════════════════════════════════════════════════════════
# STRATEGY 2: BREAKOUT HUNTER
# Support/Resistance + Volume
# ════════════════════════════════════════════════════════════════════

class BreakoutHunterStrategy:
    name = "Breakout Hunter"

    @staticmethod
    def analyze(candles: list) -> Optional[Signal]:
        if len(candles) < 30:
            return None

        closes  = [c["close"]  for c in candles]
        highs   = [c["high"]   for c in candles]
        lows    = [c["low"]    for c in candles]
        volumes = [c["volume"] for c in candles]

        price = closes[-1]
        support, resistance = Indicators.support_resistance(highs, lows, lookback=30)
        atr = Indicators.atr(highs, lows, closes, 14)[-1] or price * 0.02
        vol_sma = Indicators.volume_sma(volumes, 20)[-1] or 1
        cur_vol  = volumes[-1]
        vol_ratio= cur_vol / vol_sma if vol_sma > 0 else 1

        rsi = Indicators.rsi(closes, 14)[-1]

        proximity_to_resistance = (resistance - price) / price * 100
        proximity_to_support    = (price - support)    / price * 100

        # ── BULLISH BREAKOUT ────────────────────────────────────
        if proximity_to_resistance < 0.5 and vol_ratio > 1.5 and rsi < 75:
            # السعر على حافة المقاومة مع حجم تداول عالي
            confidence = min(90, 60 + int(vol_ratio * 10))
            entry      = resistance * 1.001  # فوق المقاومة مباشرة
            stop_loss  = support
            take_profit= entry + (entry - stop_loss) * 2.0
            rr         = (take_profit - entry) / (entry - stop_loss)

            return Signal(
                direction="long", entry=entry,
                stop_loss=stop_loss, take_profit=take_profit,
                confidence=confidence, risk_reward=rr,
                reason=f"Breakout above resistance ${resistance:.4f} | Volume {vol_ratio:.1f}x avg",
                indicators={"support": round(support,4), "resistance": round(resistance,4),
                            "vol_ratio": round(vol_ratio,2), "rsi": round(rsi,1)},
                strategy=BreakoutHunterStrategy.name
            )

        # ── BEARISH BREAKDOWN ───────────────────────────────────
        if proximity_to_support < 0.5 and vol_ratio > 1.5 and rsi > 25:
            confidence = min(90, 60 + int(vol_ratio * 10))
            entry      = support * 0.999
            stop_loss  = resistance
            take_profit= entry - (stop_loss - entry) * 2.0
            rr         = (entry - take_profit) / (stop_loss - entry)

            return Signal(
                direction="short", entry=entry,
                stop_loss=stop_loss, take_profit=take_profit,
                confidence=confidence, risk_reward=rr,
                reason=f"Breakdown below support ${support:.4f} | Volume {vol_ratio:.1f}x avg",
                indicators={"support": round(support,4), "resistance": round(resistance,4),
                            "vol_ratio": round(vol_ratio,2)},
                strategy=BreakoutHunterStrategy.name
            )

        return None


# ════════════════════════════════════════════════════════════════════
# STRATEGY 3: MEAN REVERSION
# Bollinger Bands + RSI Divergence
# ════════════════════════════════════════════════════════════════════

class MeanReversionStrategy:
    name = "Mean Reversion"

    @staticmethod
    def analyze(candles: list) -> Optional[Signal]:
        if len(candles) < 30:
            return None

        closes = [c["close"] for c in candles]
        highs  = [c["high"]  for c in candles]
        lows   = [c["low"]   for c in candles]

        price = closes[-1]
        upper, middle, lower = Indicators.bollinger_bands(closes, 20, 2.0)
        rsi14  = Indicators.rsi(closes, 14)
        stoch  = Indicators.stochastic(highs, lows, closes, 14)
        atr    = Indicators.atr(highs, lows, closes, 14)[-1] or price * 0.015

        cur_upper  = upper[-1]  or price * 1.02
        cur_lower  = lower[-1]  or price * 0.98
        cur_middle = middle[-1] or price
        cur_rsi    = rsi14[-1]
        cur_stoch  = stoch[-1]

        bb_width   = (cur_upper - cur_lower) / cur_middle
        pct_b      = (price - cur_lower) / (cur_upper - cur_lower) if (cur_upper != cur_lower) else 0.5

        # ── OVERSOLD BOUNCE (Long) ───────────────────────────────
        if (pct_b < 0.05 and           # أسفل band السفلي
            cur_rsi < 35 and           # RSI في منطقة إفراط البيع
            cur_stoch < 25):           # Stochastic كذلك
            confidence = min(85, 55 + int((35 - cur_rsi) * 1.5))
            entry      = price
            stop_loss  = price - (atr * 2.0)
            take_profit= cur_middle    # الهدف = المتوسط

            if entry <= stop_loss:
                return None
            rr = (take_profit - entry) / (entry - stop_loss)

            return Signal(
                direction="long", entry=entry,
                stop_loss=stop_loss, take_profit=take_profit,
                confidence=confidence, risk_reward=rr,
                reason=f"Price at lower Bollinger Band | RSI {cur_rsi:.1f} oversold | Stoch {cur_stoch:.1f}",
                indicators={"bb_lower": round(cur_lower,4), "bb_middle": round(cur_middle,4),
                            "rsi": round(cur_rsi,1), "stoch": round(cur_stoch,1), "pct_b": round(pct_b,2)},
                strategy=MeanReversionStrategy.name
            )

        # ── OVERBOUGHT FADE (Short) ──────────────────────────────
        if (pct_b > 0.95 and           # فوق band العلوي
            cur_rsi > 65 and           # RSI إفراط شراء
            cur_stoch > 75):           # Stochastic كذلك
            confidence = min(85, 55 + int((cur_rsi - 65) * 1.5))
            entry      = price
            stop_loss  = price + (atr * 2.0)
            take_profit= cur_middle

            if stop_loss <= entry:
                return None
            rr = (entry - take_profit) / (stop_loss - entry)

            return Signal(
                direction="short", entry=entry,
                stop_loss=stop_loss, take_profit=take_profit,
                confidence=confidence, risk_reward=rr,
                reason=f"Price at upper Bollinger Band | RSI {cur_rsi:.1f} overbought | Stoch {cur_stoch:.1f}",
                indicators={"bb_upper": round(cur_upper,4), "rsi": round(cur_rsi,1),
                            "stoch": round(cur_stoch,1), "pct_b": round(pct_b,2)},
                strategy=MeanReversionStrategy.name
            )

        return None


# ════════════════════════════════════════════════════════════════════
# STRATEGY 4: SCALPING PRO
# EMA 9/21 Crossover + Volume Spike
# ════════════════════════════════════════════════════════════════════

class ScalpingProStrategy:
    name = "Scalping Pro"

    @staticmethod
    def analyze(candles: list) -> Optional[Signal]:
        """للاستخدام على الإطارات الصغيرة (1m, 5m, 15m)"""
        if len(candles) < 25:
            return None

        closes  = [c["close"]  for c in candles]
        highs   = [c["high"]   for c in candles]
        lows    = [c["low"]    for c in candles]
        volumes = [c["volume"] for c in candles]

        price = closes[-1]
        ema9   = Indicators.ema(closes, 9)
        ema21  = Indicators.ema(closes, 21)
        rsi    = Indicators.rsi(closes, 7)  # RSI 7 للـ scalping
        atr    = Indicators.atr(highs, lows, closes, 7)[-1] or price * 0.005
        vol_sma= Indicators.volume_sma(volumes, 10)[-1] or 1
        vol_ratio = volumes[-1] / vol_sma if vol_sma > 0 else 1

        cur_ema9  = ema9[-1]
        prev_ema9 = ema9[-2]
        cur_ema21 = ema21[-1]
        prev_ema21= ema21[-2]
        cur_rsi   = rsi[-1]

        # Crossover detection
        bullish_cross = prev_ema9 <= prev_ema21 and cur_ema9 > cur_ema21
        bearish_cross = prev_ema9 >= prev_ema21 and cur_ema9 < cur_ema21

        # ── LONG SCALP ───────────────────────────────────────────
        if bullish_cross and vol_ratio > 1.3 and cur_rsi < 70:
            confidence = min(80, 60 + int(vol_ratio * 8))
            entry      = price
            stop_loss  = price - (atr * 1.2)
            take_profit= price + (atr * 2.0)
            rr         = (take_profit - entry) / (entry - stop_loss)

            return Signal(
                direction="long", entry=entry,
                stop_loss=stop_loss, take_profit=take_profit,
                confidence=confidence, risk_reward=rr,
                reason=f"EMA9 crossed above EMA21 | Volume spike {vol_ratio:.1f}x",
                indicators={"ema9": round(cur_ema9,4), "ema21": round(cur_ema21,4),
                            "rsi7": round(cur_rsi,1), "vol_ratio": round(vol_ratio,2)},
                strategy=ScalpingProStrategy.name
            )

        # ── SHORT SCALP ──────────────────────────────────────────
        if bearish_cross and vol_ratio > 1.3 and cur_rsi > 30:
            confidence = min(80, 60 + int(vol_ratio * 8))
            entry      = price
            stop_loss  = price + (atr * 1.2)
            take_profit= price - (atr * 2.0)
            rr         = (entry - take_profit) / (stop_loss - entry)

            return Signal(
                direction="short", entry=entry,
                stop_loss=stop_loss, take_profit=take_profit,
                confidence=confidence, risk_reward=rr,
                reason=f"EMA9 crossed below EMA21 | Volume spike {vol_ratio:.1f}x",
                indicators={"ema9": round(cur_ema9,4), "ema21": round(cur_ema21,4),
                            "rsi7": round(cur_rsi,1), "vol_ratio": round(vol_ratio,2)},
                strategy=ScalpingProStrategy.name
            )

        return None


# ════════════════════════════════════════════════════════════════════
# MULTI-STRATEGY ENGINE (نظام التصويت)
# ════════════════════════════════════════════════════════════════════

class MultiStrategyEngine:
    """
    يشغّل كل الاستراتيجيات ويجمع نتائجها بنظام تصويت مرجّح.
    الاستراتيجيات التي تتفق تزيد الثقة، الاختلاف يقلل.
    """

    STRATEGIES = [
        (TrendFollowingStrategy, 3),   # وزن 3 (الأهم)
        (BreakoutHunterStrategy, 2),   # وزن 2
        (MeanReversionStrategy,  2),   # وزن 2
        (ScalpingProStrategy,    1),   # وزن 1 (للتأكيد فقط)
    ]

    @staticmethod
    def analyze(candles: list, timeframes: dict = None) -> Optional[Signal]:
        """
        timeframes: {"1h": candles_1h, "4h": candles_4h, "1d": candles_1d}
        """
        long_votes  = 0
        short_votes = 0
        signals     = []
        total_weight= 0

        for strategy_cls, weight in MultiStrategyEngine.STRATEGIES:
            try:
                sig = strategy_cls.analyze(candles)
                if sig:
                    signals.append((sig, weight))
                    if sig.direction == "long":
                        long_votes  += weight * (sig.confidence / 100)
                    elif sig.direction == "short":
                        short_votes += weight * (sig.confidence / 100)
                    total_weight += weight
            except Exception as e:
                logger.warning(f"Strategy {strategy_cls.name} error: {e}")

        if not signals:
            return None

        # تحديد الاتجاه الغالب
        if long_votes > short_votes and long_votes > 0:
            direction  = "long"
            vote_ratio = long_votes / (long_votes + short_votes)
        elif short_votes > long_votes and short_votes > 0:
            direction  = "short"
            vote_ratio = short_votes / (long_votes + short_votes)
        else:
            return None  # لا اتفاق

        # الإشارات المتوافقة مع الاتجاه
        matching = [(s, w) for s, w in signals if s.direction == direction]
        if not matching:
            return None

        # حساب متوسط الأسعار المرجّح
        total_w    = sum(w for _, w in matching)
        avg_entry  = sum(s.entry      * w for s, w in matching) / total_w
        avg_sl     = sum(s.stop_loss  * w for s, w in matching) / total_w
        avg_tp     = sum(s.take_profit* w for s, w in matching) / total_w

        # الثقة = نسبة الاتفاق × متوسط الثقة الفردية
        avg_conf   = sum(s.confidence * w for s, w in matching) / total_w
        final_conf = int(min(95, avg_conf * vote_ratio * 1.1))

        if direction == "long":
            rr = (avg_tp - avg_entry) / (avg_entry - avg_sl) if (avg_entry - avg_sl) > 0 else 0
        else:
            rr = (avg_entry - avg_tp) / (avg_sl - avg_entry) if (avg_sl - avg_entry) > 0 else 0

        agreed_strategies = [s.strategy for s, _ in matching]
        reason = f"Agreement: {', '.join(agreed_strategies)} ({len(matching)}/{len(signals)} strategies)"

        return Signal(
            direction=direction,
            entry=avg_entry, stop_loss=avg_sl, take_profit=avg_tp,
            confidence=final_conf, risk_reward=round(rr, 2),
            reason=reason,
            indicators={"strategies_agreed": len(matching),
                        "vote_ratio": round(vote_ratio * 100, 1),
                        "strategies": agreed_strategies},
            strategy="Multi-Strategy"
        )
