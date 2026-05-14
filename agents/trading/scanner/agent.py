"""
Scanner Pro — مسح 500+ زوج عملات كل 60 ثانية
"""
import asyncio
from typing import Optional
from loguru import logger

from agents._shared.base_agent import BaseAgent, AgentContext, AgentResponse


class ScannerPro(BaseAgent):
    AGENT_ID = "scanner_pro"
    AGENT_NAME = "Scanner Pro 🔍"
    MODEL = "claude-haiku-4-5-20251001"  # سرعة + رخص
    MAX_TOKENS = 1500
    KNOWLEDGE_DIR = "knowledge_base/trading"

    @property
    def system_prompt(self) -> str:
        return """أنت Scanner Pro، خبير مسح أسواق التشفير.

خلفيتك: 30 سنة في غرف تداول Wall Street. شهدت انهيار 2008، انفجار dot-com، صعود البيتكوين من $1 إلى $100k. عيناك ترى ما لا يراه الآخرون.

مهمتك: مسح 500+ زوج عملات على Binance/Bybit/OKX كل 60 ثانية لاكتشاف:
- حركة Volume غير طبيعية (Volume > 3x المتوسط)
- تجمع buyers قبل اختراق resistance
- Divergence خفية في RSI
- Whale orders في order book
- Funding rates شاذة
- Breakouts محتملة

مخرجاتك دائماً منظمة هكذا:
```
🔍 SCAN RESULTS
━━━━━━━━━━━━━━━━━━━━
🎯 فرص مكتشفة: [عدد]

[لكل فرصة:]
• العملة: [SYMBOL]
• الفرصة: [نوع الإشارة]
• القوة: [1-10]
• السبب: [تفسير مختصر]
• الإجراء المقترح: [أرسل لـ Analyst Master / تجاهل]
━━━━━━━━━━━━━━━━━━━━
⚡ وقت المسح: [X] ثانية
```

قواعدك:
- فقط الإشارات القوية (8/10+) تُرسل للـ Analyst
- لا تتجاهل أي حركة Volume غير طبيعية
- الدقة أهم من السرعة — خطأ واحد يُضيّع الثقة
"""

    async def scan_markets(self, symbols: list[str] = None) -> dict:
        """مسح الأسواق وإرجاع الفرص"""
        try:
            import ccxt.async_support as ccxt
            from config.settings import settings

            exchange = ccxt.bybit({
                "sandbox": settings.bybit_testnet,
                "apiKey": settings.bybit_api_key,
                "secret": settings.bybit_secret,
            })

            if not symbols:
                markets = await exchange.load_markets()
                symbols = [s for s in markets.keys() if s.endswith("/USDT")][:50]

            opportunities = []
            for symbol in symbols[:20]:  # نبدأ بـ 20
                try:
                    ticker = await exchange.fetch_ticker(symbol)
                    ohlcv = await exchange.fetch_ohlcv(symbol, "1h", limit=24)

                    if ohlcv and len(ohlcv) >= 2:
                        avg_volume = sum(c[5] for c in ohlcv[:-1]) / len(ohlcv[:-1])
                        current_volume = ohlcv[-1][5]
                        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0

                        if volume_ratio > 2.5:
                            opportunities.append({
                                "symbol": symbol,
                                "volume_ratio": round(volume_ratio, 2),
                                "price": ticker.get("last", 0),
                                "change_24h": ticker.get("percentage", 0),
                                "signal": "high_volume"
                            })
                except Exception:
                    continue

            await exchange.close()

            opportunities.sort(key=lambda x: x["volume_ratio"], reverse=True)
            return {
                "opportunities": opportunities[:10],
                "scanned": len(symbols),
                "found": len(opportunities)
            }

        except Exception as e:
            logger.error(f"Scanner market scan error: {e}")
            return {"opportunities": [], "scanned": 0, "found": 0, "error": str(e)}

    async def analyze_opportunity(self, scan_data: dict, user_id: str = "system") -> AgentResponse:
        """تحليل نتائج المسح"""
        if not scan_data.get("opportunities"):
            context = AgentContext(
                user_id=user_id,
                user_message="لا توجد فرص مميزة الآن في السوق. هل تريد تعديل معايير المسح؟"
            )
        else:
            opps_text = "\n".join([
                f"- {o['symbol']}: volume x{o['volume_ratio']} | تغيير {o.get('change_24h', 0):.1f}%"
                for o in scan_data["opportunities"]
            ])
            context = AgentContext(
                user_id=user_id,
                user_message=f"""نتائج المسح:
فحصت {scan_data['scanned']} عملة، وجدت {scan_data['found']} فرصة محتملة:

{opps_text}

حلّل هذه النتائج وحدد أفضل 3 فرص للإرسال لـ Analyst Master."""
            )

        return await self.think(context)
