"""
TRADO Telegram Bot
يستقبل الأوامر ويرسل التنبيهات
"""
import os
import asyncio
from loguru import logger
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes


# ═══════════════════════════════════════════════════════════════
# Command Handlers
# ═══════════════════════════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🎯 أهلاً بك في TRADO، {user.first_name}!\n\n"
        f"أنا مساعدك الذكي للتداول في الكريبتو.\n\n"
        f"الأوامر المتاحة:\n"
        f"/scan - مسح السوق للفرص\n"
        f"/analyze BTC - تحليل عملة\n"
        f"/portfolio - حالة محفظتك\n"
        f"/help - المساعدة"
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 دليل الاستخدام:\n\n"
        "🔍 /scan - مسح السوق لاكتشاف الفرص\n"
        "📊 /analyze [SYMBOL] - تحليل فني (مثال: /analyze BTC)\n"
        "💼 /portfolio - حالة محفظتك الحالية\n"
        "📰 /news - أهم أخبار اليوم\n"
        "🐋 /whales - حركات الحيتان\n"
        "⚙️ /settings - الإعدادات\n"
        "💬 أو اكتب أي سؤال وسأرد عليك"
    )


async def cmd_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 جاري مسح السوق...")

    try:
        from agents.trading.scanner.agent import ScannerPro
        scanner = ScannerPro(user_id=str(update.effective_user.id))
        scan_data = await scanner.scan_markets()

        if scan_data.get("opportunities"):
            msg = "📊 الفرص المكتشفة:\n\n"
            for opp in scan_data["opportunities"][:5]:
                msg += f"• {opp['symbol']}: حجم x{opp['volume_ratio']:.1f}\n"
                msg += f"  السعر: ${opp.get('price', 0):,.2f}\n"
                msg += f"  تغيير: {opp.get('change_24h', 0):+.2f}%\n\n"
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("📭 لا توجد فرص قوية الآن. سأنبهك حالما تظهر.")
    except Exception as e:
        logger.error(f"Scan error: {e}")
        await update.message.reply_text(f"⚠️ حدث خطأ: {str(e)[:100]}")


async def cmd_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("📊 اكتب: /analyze BTC")
        return

    symbol = args[0].upper()
    if not symbol.endswith("USDT"):
        symbol = f"{symbol}/USDT"

    await update.message.reply_text(f"📊 جاري تحليل {symbol}...")

    try:
        from agents.trading.analyst.agent import AnalystMaster
        analyst = AnalystMaster(user_id=str(update.effective_user.id))
        response = await analyst.analyze(symbol, {}, user_id=str(update.effective_user.id))

        # Telegram محدود بـ 4096 حرف
        content = response.content[:3800]
        await update.message.reply_text(content, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Analyze error: {e}")
        await update.message.reply_text(f"⚠️ خطأ: {str(e)[:100]}")


async def cmd_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📰 جاري جلب الأخبار...")
    try:
        from agents.trading.news_analyst.agent import NewsAnalyst
        analyst = NewsAnalyst(user_id=str(update.effective_user.id))
        response = await analyst.analyze_news(user_id=str(update.effective_user.id))
        await update.message.reply_text(response.content[:3800])
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطأ: {str(e)[:100]}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رد على أي رسالة عادية باستخدام Analyst Master"""
    text = update.message.text
    try:
        from agents.trading.analyst.agent import AnalystMaster
        from agents._shared.base_agent import AgentContext

        analyst = AnalystMaster(user_id=str(update.effective_user.id))
        ctx = AgentContext(
            user_id=str(update.effective_user.id),
            user_message=text
        )
        response = await analyst.think(ctx)
        await update.message.reply_text(response.content[:3800])
    except Exception as e:
        logger.error(f"Message error: {e}")
        await update.message.reply_text("⚠️ عذراً، حدث خطأ. حاول مرة أخرى.")


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return

    app = Application.builder().token(token).build()

    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("scan", cmd_scan))
    app.add_handler(CommandHandler("analyze", cmd_analyze))
    app.add_handler(CommandHandler("news", cmd_news))

    # Free-text messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🤖 TRADO Telegram Bot starting...")
    await app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    asyncio.run(main())
