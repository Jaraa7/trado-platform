"""
Regime Detector — تحديد حالة السوق الحقيقية
Bull / Bear / Sideways / Volatile / Crash
"""
from dataclasses import dataclass
from enum import Enum
from agents._shared.base_agent import BaseAgent, AgentContext, AgentResponse


class MarketRegime(str, Enum):
    BULL_STRONG    = "bull_strong"      # صعود قوي
    BULL_WEAK      = "bull_weak"        # صعود ضعيف
    SIDEWAYS       = "sideways"         # تذبذب جانبي
    BEAR_WEAK      = "bear_weak"        # هبوط خفيف
    BEAR_STRONG    = "bear_strong"      # هبوط حاد
    VOLATILE       = "volatile"         # تذبذب عالي
    CRASH          = "crash"            # انهيار


@dataclass
class RegimeResult:
    regime: MarketRegime
    confidence: float           # 0-1
    trend_strength: float       # ADX value
    volatility: str             # low / normal / high / extreme
    recommended_strategies: list[str]
    avoid_strategies: list[str]
    description: str


class RegimeDetector(BaseAgent):
    AGENT_ID = "regime_detector"
    AGENT_NAME = "Regime Detector 🌊"
    MODEL = "claude-haiku-4-5-20251001"
    MAX_TOKENS = 1000

    @property
    def system_prompt(self) -> str:
        return """أنت Regime Detector، خبير تحديد حالة السوق.

خلفيتك: 30 سنة رأيت كل أنواع الأسواق. تستخدم Hidden Markov Models ومؤشرات متعددة.

مهمتك: تحديد "مزاج" السوق الحقيقي بدقة 78%+.

الأنواع الممكنة:
🟢 BULL_STRONG    — صعود مستمر + volume عالي + momentum قوي
🟡 BULL_WEAK      — صعود بطيء + volume متوسط
⬜ SIDEWAYS       — تذبذب بين نطاق محدد
🟠 BEAR_WEAK      — هبوط خفيف + volume منخفض
🔴 BEAR_STRONG    — هبوط حاد + panic selling
⚡ VOLATILE       — تذبذب عشوائي + uncertainty عالية
💥 CRASH          — انهيار مفاجئ + volume خيالي

مخرجاتك:
```
🌊 REGIME ANALYSIS
━━━━━━━━━━━━━━━━━━━━
📊 الحالة: [REGIME]
🎯 الثقة: [X]%
💪 قوة الترند (ADX): [X]
⚡ Volatility: [low/normal/high/extreme]

✅ استراتيجيات مناسبة:
  • [strategy 1]
  • [strategy 2]

❌ تجنب:
  • [strategy to avoid]

💡 الملخص: [جملة واحدة]
```"""

    def quick_regime(self, ohlcv_data: list, adx: float = 0, atr_ratio: float = 0) -> RegimeResult:
        """تحديد سريع للـ regime من البيانات"""
        if not ohlcv_data or len(ohlcv_data) < 10:
            return RegimeResult(
                regime=MarketRegime.SIDEWAYS,
                confidence=0.5,
                trend_strength=20,
                volatility="normal",
                recommended_strategies=["range_trading"],
                avoid_strategies=["trend_following"],
                description="بيانات غير كافية — نفترض Sideways"
            )

        closes = [c[4] for c in ohlcv_data]
        volumes = [c[5] for c in ohlcv_data]

        # حساب مبسّط
        price_change = (closes[-1] - closes[0]) / closes[0] * 100
        avg_vol = sum(volumes[:-5]) / len(volumes[:-5]) if len(volumes) > 5 else 1
        recent_vol = sum(volumes[-5:]) / 5
        vol_ratio = recent_vol / avg_vol if avg_vol > 0 else 1

        # تحديد الـ regime
        if adx > 30 and price_change > 5:
            regime = MarketRegime.BULL_STRONG
            strategies = ["trend_following", "momentum", "breakout"]
            avoid = ["mean_reversion", "range_trading"]
            confidence = 0.80
        elif adx > 20 and price_change > 2:
            regime = MarketRegime.BULL_WEAK
            strategies = ["swing_trading", "dip_buying"]
            avoid = ["short_selling"]
            confidence = 0.70
        elif adx > 30 and price_change < -5:
            regime = MarketRegime.BEAR_STRONG
            strategies = ["short_selling", "cash_position"]
            avoid = ["buying_dips", "trend_following_long"]
            confidence = 0.80
        elif price_change < -2:
            regime = MarketRegime.BEAR_WEAK
            strategies = ["cautious_buying", "hedging"]
            avoid = ["high_leverage"]
            confidence = 0.65
        elif atr_ratio > 2.0 or vol_ratio > 3:
            regime = MarketRegime.VOLATILE
            strategies = ["range_trading", "low_position_size"]
            avoid = ["trend_following", "high_leverage"]
            confidence = 0.75
        else:
            regime = MarketRegime.SIDEWAYS
            strategies = ["range_trading", "mean_reversion", "grid_trading"]
            avoid = ["trend_following"]
            confidence = 0.72

        volatility = "high" if vol_ratio > 2 else "normal" if vol_ratio > 0.8 else "low"

        return RegimeResult(
            regime=regime,
            confidence=confidence,
            trend_strength=adx,
            volatility=volatility,
            recommended_strategies=strategies,
            avoid_strategies=avoid,
            description=f"تغيير السعر {price_change:+.1f}% | حجم x{vol_ratio:.1f}"
        )

    async def analyze(self, market_data: dict, user_id: str = "system") -> AgentResponse:
        regime = self.quick_regime(
            market_data.get("ohlcv", []),
            market_data.get("adx", 25),
            market_data.get("atr_ratio", 1.0)
        )

        context = AgentContext(
            user_id=user_id,
            user_message=f"""حدد حالة السوق:

البيانات: {market_data}

التحليل الأولي:
- الحالة المقترحة: {regime.regime.value}
- الثقة: {regime.confidence*100:.0f}%
- Volatility: {regime.volatility}
- الاستراتيجيات المناسبة: {regime.recommended_strategies}

قدم تقريرك الكامل.""",
            market_data=market_data
        )
        return await self.think(context)
