"""
Pattern Recognition — التعرف الآلي على Chart Patterns
"""
from dataclasses import dataclass
from agents._shared.base_agent import BaseAgent, AgentContext, AgentResponse


@dataclass
class ChartPattern:
    name: str
    type: str           # reversal / continuation
    reliability: float  # 0-1
    target_pct: float   # الهدف كنسبة مئوية
    confirmation: str   # ما يؤكد النموذج
    timeframe: str


class PatternRecognition(BaseAgent):
    AGENT_ID = "pattern_recognition"
    AGENT_NAME = "Pattern Recognition 🔮"
    MODEL = "claude-haiku-4-5-20251001"
    MAX_TOKENS = 1500

    # قاموس النماذج
    PATTERN_CATALOG = {
        "head_and_shoulders": ChartPattern("Head & Shoulders", "reversal", 0.80, -15, "Neckline break", "daily"),
        "double_top": ChartPattern("Double Top", "reversal", 0.75, -10, "Support break", "4h"),
        "double_bottom": ChartPattern("Double Bottom", "reversal", 0.75, 10, "Resistance break", "4h"),
        "ascending_triangle": ChartPattern("Ascending Triangle", "continuation", 0.72, 8, "Upper break", "4h"),
        "descending_triangle": ChartPattern("Descending Triangle", "continuation", 0.70, -8, "Lower break", "4h"),
        "bull_flag": ChartPattern("Bull Flag", "continuation", 0.78, 12, "Flag break up", "1h"),
        "bear_flag": ChartPattern("Bear Flag", "continuation", 0.76, -12, "Flag break down", "1h"),
        "cup_handle": ChartPattern("Cup & Handle", "continuation", 0.82, 15, "Handle break", "daily"),
        "wedge_rising": ChartPattern("Rising Wedge", "reversal", 0.68, -10, "Lower trendline break", "4h"),
        "wedge_falling": ChartPattern("Falling Wedge", "continuation", 0.70, 10, "Upper trendline break", "4h"),
        "symmetrical_triangle": ChartPattern("Symmetrical Triangle", "neutral", 0.65, 8, "Either side break", "4h"),
        "rounding_bottom": ChartPattern("Rounding Bottom", "reversal", 0.72, 20, "Resistance break", "weekly"),
    }

    # نماذج Harmonic
    HARMONIC_PATTERNS = {
        "gartley": {"xab": 0.618, "abc": 0.382, "bcd": 1.272, "xad": 0.786},
        "bat": {"xab": 0.382, "abc": 0.382, "bcd": 1.618, "xad": 0.886},
        "butterfly": {"xab": 0.786, "abc": 0.382, "bcd": 1.618, "xad": 1.272},
        "crab": {"xab": 0.382, "abc": 0.382, "bcd": 2.618, "xad": 1.618},
    }

    @property
    def system_prompt(self) -> str:
        return """أنت Pattern Recognition، متخصص التعرف على نماذج الرسم البياني.

خبرتك: تعرف على 200+ نموذج يدوياً وآلياً. من الكلاسيكية (H&S, Triangles, Flags) إلى Harmonic (Gartley, Bat, Butterfly, Crab).

معاييرك للجودة:
- A+: نموذج واضح + تأكيد volume + timeframe عالي
- A:  نموذج واضح + timeframe متوسط
- B:  نموذج محتمل + تأكيد ناقص
- C:  نموذج ضعيف → لا توصية

مخرجاتك:
```
🔮 PATTERN ANALYSIS
━━━━━━━━━━━━━━━━━━━━
📐 النموذج: [Pattern Name]
🔄 النوع: [Reversal/Continuation]
⭐ الجودة: [A+/A/B/C]
✅ الموثوقية: [X]%

📊 التفاصيل:
  Timeframe: [X]
  المرحلة: [forming/near_completion/completed]
  الهدف: [+/-X%] عند [السعر]
  Stop: [سعر الإلغاء]

✅ تأكيد: [ما يلزم لتأكيد النموذج]
⚠️  إلغاء: [متى يُلغى النموذج]
```"""

    def identify_basic_pattern(self, highs: list, lows: list, closes: list) -> list[str]:
        """تعرف مبسّط على النماذج من البيانات الخام"""
        patterns = []

        if len(highs) < 20 or len(lows) < 20:
            return ["بيانات غير كافية"]

        recent_high = max(highs[-20:])
        recent_low = min(lows[-20:])
        price_range = recent_high - recent_low

        # Double Top
        top_indices = [i for i, h in enumerate(highs[-20:]) if h > recent_high * 0.98]
        if len(top_indices) >= 2 and top_indices[-1] - top_indices[0] > 5:
            patterns.append("double_top")

        # Double Bottom
        bottom_indices = [i for i, l in enumerate(lows[-20:]) if l < recent_low * 1.02]
        if len(bottom_indices) >= 2 and bottom_indices[-1] - bottom_indices[0] > 5:
            patterns.append("double_bottom")

        # Higher highs and higher lows (bull flag potential)
        if len(closes) >= 10:
            last_5_closes = closes[-5:]
            prev_5_closes = closes[-10:-5]
            if min(last_5_closes) > min(prev_5_closes) and max(last_5_closes) < max(prev_5_closes):
                patterns.append("bull_flag")

        return patterns if patterns else ["no_clear_pattern"]

    async def analyze(self, symbol: str, ohlcv: list, user_id: str = "system") -> AgentResponse:
        highs = [c[2] for c in ohlcv] if ohlcv else []
        lows = [c[3] for c in ohlcv] if ohlcv else []
        closes = [c[4] for c in ohlcv] if ohlcv else []

        detected = self.identify_basic_pattern(highs, lows, closes)
        patterns_info = "\n".join([
            f"- {p}: {self.PATTERN_CATALOG[p].type if p in self.PATTERN_CATALOG else 'unknown'}"
            for p in detected
        ])

        context = AgentContext(
            user_id=user_id,
            user_message=f"""حلّل الرسم البياني لـ {symbol}:

النماذج المكتشفة مبدئياً:
{patterns_info}

آخر {len(ohlcv)} شمعة متاحة.

المطلوب:
1. تأكيد أو نفي النماذج المكتشفة
2. هل هناك نماذج أخرى لم تُكتشف؟
3. النموذج الأقوى وهدفه
4. هل يستحق التداول؟"""
        )
        return await self.think(context)
