"""
🔄 TradoAI Background Workers
يعملون 24/7 لفحص السوق + توليد الإشارات + إرسال التنبيهات
"""
import asyncio
from datetime import datetime
from loguru import logger
from db.client import get_supabase, SignalDB, UserDB
from cache import Cache, SharedContext


# ════════════════════════════════════════════════════════════════════
# Market Scanner Worker (يعمل كل دقيقة)
# ════════════════════════════════════════════════════════════════════

async def worker_market_scanner():
    """يفحص السوق كل 60 ثانية لاكتشاف الفرص"""
    logger.info("🔍 Market Scanner Worker started")

    while True:
        try:
            from agents.trading.scanner.agent import ScannerPro
            scanner = ScannerPro(user_id="system")

            scan_data = await scanner.scan_markets()
            opportunities = scan_data.get("opportunities", [])

            # خزّن النتائج في shared context (للجميع)
            await SharedContext.set_market_scan(opportunities)

            logger.info(f"📊 Scanner: found {len(opportunities)} opportunities")

            # توليد إشارات للفرص القوية
            for opp in opportunities[:5]:    # أعلى 5 فقط
                await _generate_signal_for(opp)

        except Exception as e:
            logger.error(f"Scanner worker error: {e}")

        await asyncio.sleep(60)


# ════════════════════════════════════════════════════════════════════
# Signal Generator (تحليل عميق للفرص القوية)
# ════════════════════════════════════════════════════════════════════

async def _generate_signal_for(opportunity: dict):
    """تحليل عميق + إنشاء إشارة في DB"""
    symbol = opportunity.get("symbol")
    if not symbol:
        return

    # تحقق من عدم وجود إشارة حديثة (لتجنب التكرار)
    cache_key = Cache.make_key("signal_generated", symbol)
    if await Cache.get(cache_key):
        return

    try:
        from agents.trading.analyst.agent import AnalystMaster
        from agents.trading.risk_guardian.agent import RiskGuardian, TradeProposal

        analyst = AnalystMaster(user_id="system")
        response = await analyst.analyze(symbol, opportunity, user_id="system")

        if not response.success:
            return

        # تقدير الـ entry/SL/TP من التحليل (مبسّط)
        price = opportunity.get("price", 0)
        if price <= 0:
            return

        # Default: 3% SL, 6% TP
        entry = price
        sl = price * 0.97
        tp = price * 1.06

        # احفظ في DB
        SignalDB.create(
            symbol=symbol,
            direction="long",
            entry=entry,
            sl=sl,
            tp=tp,
            confidence=75,
            ai_analysis=response.content[:5000],
            agent_id="analyst_master",
            ai_tokens_used=response.tokens_used,
            ai_cost_usd=response.cost_usd,
        )

        # منع التكرار لـ 30 دقيقة
        await Cache.set(cache_key, True, ttl=1800)

        # ابعث للمستخدمين
        await _broadcast_signal(symbol, entry, sl, tp)

    except Exception as e:
        logger.error(f"Signal generation failed for {symbol}: {e}")


# ════════════════════════════════════════════════════════════════════
# Signal Broadcaster (يرسل للمشتركين)
# ════════════════════════════════════════════════════════════════════

async def _broadcast_signal(symbol: str, entry: float, sl: float, tp: float):
    """يرسل الإشارة لكل المشتركين النشطين"""
    sb = get_supabase(service_role=True)

    # جلب المشتركين الذين لديهم notifications مفعلة
    users = sb.table("user_settings") \
        .select("user_id") \
        .eq("notify_signals", True) \
        .execute()

    for user_setting in users.data:
        user_id = user_setting["user_id"]
        try:
            user = UserDB.get_by_id(user_id)
            if not user or user.get("status") != "active":
                continue

            # إنشاء notification
            sb.table("notifications").insert({
                "user_id": user_id,
                "type": "signal",
                "title": f"إشارة جديدة: {symbol}",
                "body": f"شراء عند ${entry:,.2f} | SL: ${sl:,.2f} | TP: ${tp:,.2f}",
                "data": {"symbol": symbol, "entry": entry, "sl": sl, "tp": tp}
            }).execute()

            # أرسل في Telegram لو مفعّل
            if user.get("telegram_chat_id"):
                await _send_telegram(
                    user["telegram_chat_id"],
                    f"🎯 إشارة جديدة!\n\n"
                    f"💎 {symbol}\n"
                    f"📥 الدخول: ${entry:,.2f}\n"
                    f"🛑 وقف الخسارة: ${sl:,.2f}\n"
                    f"🎯 الهدف: ${tp:,.2f}\n"
                    f"📊 R:R: {abs(tp-entry)/abs(entry-sl):.2f}"
                )
        except Exception as e:
            logger.error(f"Broadcast failed for user {user_id[:8]}: {e}")


# ════════════════════════════════════════════════════════════════════
# Telegram Sender
# ════════════════════════════════════════════════════════════════════

async def _send_telegram(chat_id: int, text: str):
    """إرسال رسالة Telegram"""
    import os
    import httpx

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML"
                }
            )
    except Exception as e:
        logger.error(f"Telegram send error: {e}")


# ════════════════════════════════════════════════════════════════════
# Trade Monitor (يفحص الصفقات المفتوحة)
# ════════════════════════════════════════════════════════════════════

async def worker_trade_monitor():
    """يفحص الصفقات المفتوحة كل 30 ثانية"""
    logger.info("📈 Trade Monitor Worker started")

    while True:
        try:
            sb = get_supabase(service_role=True)
            open_trades = sb.table("trades").select("*").eq("status", "open").execute()

            for trade in open_trades.data:
                await _check_trade(trade)

        except Exception as e:
            logger.error(f"Trade monitor error: {e}")

        await asyncio.sleep(30)


async def _check_trade(trade: dict):
    """فحص صفقة واحدة - هل بلغت TP أو SL؟"""
    symbol = trade["symbol"]
    current_price = await SharedContext.get_price(symbol)
    if not current_price:
        return

    price = current_price.get("price", 0)
    sl = float(trade.get("stop_loss") or 0)
    tp = float(trade.get("take_profit") or 0)

    if trade["direction"] == "long":
        if price <= sl:
            await _close_trade(trade, price, reason="stop_loss")
        elif price >= tp:
            await _close_trade(trade, price, reason="take_profit")


async def _close_trade(trade: dict, exit_price: float, reason: str):
    """إغلاق صفقة وحساب الـ PnL"""
    from db.client import TradeDB

    entry = float(trade["entry_price"])
    qty = float(trade["quantity"])

    if trade["direction"] == "long":
        pnl = (exit_price - entry) * qty
    else:
        pnl = (entry - exit_price) * qty

    TradeDB.close(trade["id"], exit_price, pnl)

    # إشعار للمستخدم
    user = UserDB.get_by_id(trade["user_id"])
    if user and user.get("telegram_chat_id"):
        emoji = "🟢" if pnl > 0 else "🔴"
        await _send_telegram(
            user["telegram_chat_id"],
            f"{emoji} صفقة مغلقة: {trade['symbol']}\n"
            f"السبب: {reason}\n"
            f"PnL: ${pnl:+,.2f}"
        )


# ════════════════════════════════════════════════════════════════════
# Subscription Renewal Checker
# ════════════════════════════════════════════════════════════════════

async def worker_subscription_checker():
    """يفحص الاشتراكات المنتهية يومياً"""
    logger.info("📅 Subscription Checker Worker started")

    while True:
        try:
            sb = get_supabase(service_role=True)
            from datetime import timedelta

            # اشتراكات تنتهي خلال 3 أيام
            soon = (datetime.utcnow() + timedelta(days=3)).isoformat()
            expiring = sb.table("subscriptions") \
                .select("*, users(*)") \
                .eq("status", "active") \
                .lte("current_period_end", soon) \
                .execute()

            for sub in expiring.data:
                user = sub.get("users", {})
                if user.get("telegram_chat_id"):
                    await _send_telegram(
                        user["telegram_chat_id"],
                        f"⏰ تذكير: اشتراك {sub['tier']} ينتهي قريباً\n"
                        f"احرص على تجديده لمواصلة الخدمة بدون انقطاع."
                    )

        except Exception as e:
            logger.error(f"Subscription checker error: {e}")

        await asyncio.sleep(86400)    # كل 24 ساعة


# ════════════════════════════════════════════════════════════════════
# Main Workers Entry Point
# ════════════════════════════════════════════════════════════════════

async def start_workers():
    """تشغيل جميع الـ workers بالتوازي"""
    logger.info("🚀 Starting all TradoAI workers...")

    await asyncio.gather(
        worker_market_scanner(),
        worker_trade_monitor(),
        worker_subscription_checker(),
    )


if __name__ == "__main__":
    asyncio.run(start_workers())
