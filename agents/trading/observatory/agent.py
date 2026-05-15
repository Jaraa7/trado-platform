"""
Observatory — العين التي لا تنام. مراقبة كل شيء.
"""
import asyncio
from typing import Optional
from datetime import datetime
from loguru import logger
from agents._shared.base_agent import BaseAgent, AgentContext, AgentResponse


class Observatory(BaseAgent):
    AGENT_ID = "observatory"
    AGENT_NAME = "Observatory 👁️"
    MODEL = "claude-haiku-4-5"
    MAX_TOKENS = 1000

    def __init__(self, user_id: str = "system"):
        super().__init__(user_id)
        self._positions = {}
        self._daily_pnl = 0.0
        self._alerts_sent = []

    @property
    def system_prompt(self) -> str:
        return """أنت Observatory، العين التي لا تنام في TRADO.

تراقب كل شيء في الوقت الفعلي:
- P&L لكل صفقة وللحساب ككل
- الصفقات المفتوحة وأدائها
- أداء كل agent
- أي شذوذ في الأسعار أو الحجم

تُنبّه فوراً عند:
⚠️ خسارة > 1.5% في صفقة واحدة
🚨 خسارة يومية > 4%
🔴 drawdown > 10%
❗ فشل execution أو API error

تقاريرك مختصرة ودقيقة."""

    async def update_position(self, symbol: str, entry: float, current: float, size: float, direction: str):
        """تحديث موقف مفتوح"""
        if direction == "long":
            pnl_pct = (current - entry) / entry * 100
        else:
            pnl_pct = (entry - current) / entry * 100

        pnl_usd = size * pnl_pct / 100

        self._positions[symbol] = {
            "entry": entry,
            "current": current,
            "size": size,
            "direction": direction,
            "pnl_pct": round(pnl_pct, 3),
            "pnl_usd": round(pnl_usd, 2),
            "updated_at": datetime.utcnow().isoformat()
        }

        self._daily_pnl += pnl_usd

        # فحص التنبيهات
        await self._check_alerts(symbol, pnl_pct)

        # حفظ في الذاكرة
        await self.memory.remember("positions", self._positions, ttl_seconds=86400)
        await self.memory.remember("daily_pnl", self._daily_pnl, ttl_seconds=86400)

    async def _check_alerts(self, symbol: str, pnl_pct: float):
        """فحص التنبيهات الحرجة"""
        from config.settings import settings

        if pnl_pct < -1.5:
            await self._send_alert(
                f"⚠️ {symbol}: خسارة {pnl_pct:.2f}% تجاوزت تحذير -1.5%",
                level="warning"
            )

        total_pnl_pct = self._daily_pnl  # مبسّط
        if total_pnl_pct < -settings.max_daily_loss * 100 * 0.7:
            await self._send_alert(
                f"🚨 الخسارة اليومية وصلت {total_pnl_pct:.2f}% — اقتراب من الحد اليومي!",
                level="critical"
            )

    async def _send_alert(self, message: str, level: str = "info"):
        """إرسال تنبيه عبر Telegram"""
        logger.warning(f"OBSERVATORY ALERT [{level.upper()}]: {message}")
        self._alerts_sent.append({
            "message": message,
            "level": level,
            "timestamp": datetime.utcnow().isoformat()
        })

        try:
            from config.settings import settings
            if settings.telegram_bot_token and settings.telegram_admin_chat_id:
                import httpx
                emoji = "⚠️" if level == "warning" else "🚨" if level == "critical" else "ℹ️"
                text = f"{emoji} TRADO Alert\n\n{message}"
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                        json={"chat_id": settings.telegram_admin_chat_id, "text": text}
                    )
        except Exception as e:
            logger.error(f"Telegram alert failed: {e}")

    async def get_dashboard(self, user_id: str = "system") -> AgentResponse:
        """توليد تقرير الـ dashboard"""
        positions_text = ""
        if self._positions:
            for sym, pos in self._positions.items():
                emoji = "📈" if pos["pnl_pct"] > 0 else "📉"
                positions_text += f"\n{emoji} {sym}: {pos['pnl_pct']:+.2f}% | ${pos['pnl_usd']:+.2f}"

        context = AgentContext(
            user_id=user_id,
            user_message=f"""حالة المحفظة الآن:

الصفقات المفتوحة:{positions_text or ' لا توجد صفقات مفتوحة'}

P&L اليوم: ${self._daily_pnl:+.2f}
عدد التنبيهات: {len(self._alerts_sent)}

قدم تقرير موجز عن الحالة الحالية."""
        )
        return await self.think(context)
