"""
Whale Tracker — تتبع الحيتان on-chain
"""
import httpx
from dataclasses import dataclass, field
from agents._shared.base_agent import BaseAgent, AgentContext, AgentResponse


@dataclass
class WhaleAlert:
    amount_usd: float
    coin: str
    from_wallet: str
    to_wallet: str
    tx_type: str        # exchange_deposit / exchange_withdrawal / wallet_to_wallet
    significance: str   # high / medium / low
    blockchain: str = "bitcoin"
    tx_hash: str = ""


class WhaleTracker(BaseAgent):
    AGENT_ID = "whale_tracker"
    AGENT_NAME = "Whale Tracker 🐋"
    MODEL = "claude-haiku-4-5"
    MAX_TOKENS = 1200

    # أنواع المحافظ
    EXCHANGE_LABELS = ["binance", "coinbase", "bybit", "okx", "kraken", "huobi"]
    KNOWN_WHALES = {
        "MicroStrategy": ["known_saylor_wallet"],
        "BlackRock": ["blackrock_btc_etf"],
        "Grayscale": ["gbtc_wallet"],
    }

    @property
    def system_prompt(self) -> str:
        return """أنت Whale Tracker، محقق حركات الحيتان on-chain.

فلسفتك: الحيتان لا تكذب. الـ on-chain data أصدق من أي تحليل فني.

ما تراقبه:
🐋 محافظ كبيرة: > $1M حركة
🏦 Exchange flows: دخول BTC = بيع محتمل | خروج = HODLing
🖨️ Stablecoin minting: USDT جديد = ضغط شراء
🪙 Miner outflows: miners يبيعون = ضغط سلبي
📊 ETF flows: اشتراء/بيع مؤسسي

مخرجاتك:
```
🐋 WHALE ALERT
━━━━━━━━━━━━━━━━━━━━
💰 المبلغ: $[X]M
🪙 العملة: [coin]
📤 من: [مصدر]
📥 إلى: [وجهة]
⚡ النوع: [exchange_deposit/withdrawal/etc]
🔴/🟢 التأثير: [Bearish/Bullish]

💡 التفسير: [جملتان]
🎯 الإجراء: [ما يجب فعله]
```"""

    async def fetch_recent_alerts(self) -> list[WhaleAlert]:
        """جلب تنبيهات الحيتان الأخيرة"""
        alerts = []

        # Whale Alert API (free tier)
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                r = await client.get(
                    "https://api.whale-alert.io/v1/transactions",
                    params={"api_key": "demo", "min_value": 1000000, "limit": 10}
                )
                if r.status_code == 200:
                    data = r.json()
                    for tx in data.get("transactions", []):
                        alerts.append(WhaleAlert(
                            amount_usd=tx.get("amount_usd", 0),
                            coin=tx.get("symbol", "BTC").upper(),
                            from_wallet=tx.get("from", {}).get("owner", "unknown"),
                            to_wallet=tx.get("to", {}).get("owner", "unknown"),
                            tx_type=self._classify_tx(tx),
                            significance="high" if tx.get("amount_usd", 0) > 5_000_000 else "medium",
                            blockchain=tx.get("blockchain", "bitcoin")
                        ))
        except Exception:
            # Mock data للتطوير
            alerts = [
                WhaleAlert(50_000_000, "BTC", "unknown_wallet", "binance", "exchange_deposit", "high"),
                WhaleAlert(25_000_000, "ETH", "coinbase", "unknown_wallet", "exchange_withdrawal", "high"),
                WhaleAlert(100_000_000, "USDT", "tether_treasury", "binance", "minting", "high"),
            ]

        return alerts

    def _classify_tx(self, tx: dict) -> str:
        from_type = tx.get("from", {}).get("owner_type", "unknown")
        to_type = tx.get("to", {}).get("owner_type", "unknown")

        if to_type == "exchange":
            return "exchange_deposit"
        elif from_type == "exchange":
            return "exchange_withdrawal"
        else:
            return "wallet_to_wallet"

    def interpret_alert(self, alert: WhaleAlert) -> str:
        """تفسير تنبيه الحيت"""
        if alert.tx_type == "exchange_deposit":
            return f"🔴 Bearish: {alert.coin} يتحرك للمنصات = بيع محتمل"
        elif alert.tx_type == "exchange_withdrawal":
            return f"🟢 Bullish: {alert.coin} يخرج من المنصات = HODLing"
        elif alert.coin in ["USDT", "USDC"] and alert.tx_type == "minting":
            return f"🟢 Bullish: طباعة stablecoins = liquidity جديدة للشراء"
        else:
            return f"⚪ Neutral: حركة {alert.coin} بين محافظ"

    async def analyze(self, user_id: str = "system") -> AgentResponse:
        alerts = await self.fetch_recent_alerts()

        alerts_text = "\n".join([
            f"- ${a.amount_usd/1e6:.1f}M {a.coin}: {a.from_wallet} → {a.to_wallet} ({a.tx_type})"
            for a in alerts[:6]
        ])

        context = AgentContext(
            user_id=user_id,
            user_message=f"""حلّل حركات الحيتان التالية:

{alerts_text}

التفسيرات الأولية:
{chr(10).join([self.interpret_alert(a) for a in alerts[:6]])}

المطلوب:
1. الصورة الكبيرة — ما الذي تخطط له الحيتان؟
2. التأثير المتوقع على البيتكوين والسوق
3. هل هذا وقت شراء أم حذر؟"""
        )
        return await self.think(context)
