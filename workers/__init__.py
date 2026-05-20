"""
🔄 TradoAI — Background Workers
يعمل 24/7 لتحديث البيانات، توليد الإشارات، وإرسال التنبيهات
"""
import asyncio
from loguru import logger

from data_sources.market   import PriceSource, OHLCVSource, DerivativesSource, SentimentSource
from data_sources.news     import NewsAggregator
from data_sources.whales   import LargeTrades, LongShortSource
from data_sources.extended import OnChainSource, RedditSentiment, ComprehensiveAnalyzer, WebSocketManager
from strategies.engine     import MultiStrategyEngine
from cache                 import Cache, SharedContext

DEFAULT_SYMBOLS = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT",
    "BNB/USDT", "XRP/USDT", "AVAX/USDT",
    "DOGE/USDT", "ADA/USDT",
]


# ════════════════════════════════════════════════════════════════════
# Worker 1: WebSocket — أسعار حية (مستمر)
# ════════════════════════════════════════════════════════════════════
async def worker_websocket():
    logger.info("🔌 WebSocket Worker started")
    ws = WebSocketManager()

    async def on_price(data: dict):
        await SharedContext.set_price(data["symbol"], data)

    ws.on_price(on_price)
    await ws.start(DEFAULT_SYMBOLS)


# ════════════════════════════════════════════════════════════════════
# Worker 2: Market Scanner — إشارات (كل 60 ثانية)
# ════════════════════════════════════════════════════════════════════
async def worker_market_scanner():
    logger.info("🔍 Market Scanner started")
    while True:
        try:
            await _scan_and_signal()
        except Exception as e:
            logger.error(f"Scanner error: {e}")
        await asyncio.sleep(60)


async def _scan_and_signal():
    for symbol in DEFAULT_SYMBOLS:
        try:
            candles_1h = await OHLCVSource.get(symbol, "1h", 200)
            candles_4h = await OHLCVSource.get(symbol, "4h", 100)
            if len(candles_1h) < 60:
                continue

            signal = MultiStrategyEngine.analyze(candles_1h)
            if not signal or signal.confidence < 65:
                continue

            # تحقق من عدم وجود إشارة حديثة
            ck = Cache.make_key("signal_sent", symbol)
            if await Cache.get(ck):
                continue

            # تأكيد 4H
            signal_4h = MultiStrategyEngine.analyze(candles_4h)
            if signal_4h and signal_4h.direction == signal.direction:
                signal.confidence = min(95, signal.confidence + 8)
                signal.reason += f" | 4H confirms: {signal_4h.strategy}"

            # حفظ في DB
            try:
                from db.client import get_supabase
                sb = get_supabase(service_role=True)
                sb.table("signals").insert({
                    "symbol":      symbol,
                    "direction":   signal.direction,
                    "entry_price": signal.entry,
                    "stop_loss":   signal.stop_loss,
                    "take_profit": signal.take_profit,
                    "confidence":  signal.confidence,
                    "strategy":    signal.strategy,
                    "reason":      signal.reason,
                }).execute()
            except Exception as e:
                logger.warning(f"Signal DB insert: {e}")

            # إرسال للمستخدمين
            await _broadcast_signal(symbol, signal.to_dict())

            # منع التكرار 30 دقيقة
            await Cache.set(ck, True, ttl=1800)
            logger.info(f"📊 Signal: {symbol} {signal.direction} conf={signal.confidence}%")

        except Exception as e:
            logger.warning(f"Signal error {symbol}: {e}")


# ════════════════════════════════════════════════════════════════════
# Worker 3: Data Refresh (كل 5 دقائق)
# ════════════════════════════════════════════════════════════════════
async def worker_data_refresh():
    logger.info("📡 Data Refresh Worker started")
    while True:
        try:
            await asyncio.gather(
                PriceSource.get_multi(DEFAULT_SYMBOLS),
                _refresh_derivatives(),
                _refresh_sentiment(),
                return_exceptions=True
            )
            logger.debug(f"✅ Data refreshed for {len(DEFAULT_SYMBOLS)} symbols")
        except Exception as e:
            logger.error(f"Data refresh error: {e}")
        await asyncio.sleep(300)


async def _refresh_derivatives():
    for sym in ["BTC/USDT", "ETH/USDT", "SOL/USDT"]:
        await asyncio.gather(
            DerivativesSource.get_funding(sym),
            DerivativesSource.get_long_short(sym),
            DerivativesSource.get_open_interest(sym),
            return_exceptions=True
        )


async def _refresh_sentiment():
    await asyncio.gather(
        SentimentSource.get_fear_greed(),
        SentimentSource.get_trending(),
        SentimentSource.get_global_market(),
        return_exceptions=True
    )


# ════════════════════════════════════════════════════════════════════
# Worker 4: Market Report (كل 30 دقيقة)
# ════════════════════════════════════════════════════════════════════
async def worker_market_report():
    logger.info("📋 Market Report Worker started")
    while True:
        try:
            report = await ComprehensiveAnalyzer.full_market_report()
            await Cache.set(Cache.make_key("market_report", "latest"), report, ttl=1800)
            logger.info(f"📋 Report: {report.get('overall_sentiment','?')} score={report.get('overall_score','?')}")
        except Exception as e:
            logger.error(f"Market report error: {e}")
        await asyncio.sleep(1800)


# ════════════════════════════════════════════════════════════════════
# Worker 5: News (كل 10 دقائق)
# ════════════════════════════════════════════════════════════════════
async def worker_news():
    logger.info("📰 News Worker started")
    while True:
        try:
            summary = await NewsAggregator.get_summary()
            for news in summary.get("top_news", [])[:3]:
                if news.get("sentiment") in ["bullish", "bearish"]:
                    ck = Cache.make_key("news_sent", news.get("url","")[:50])
                    if not await Cache.get(ck):
                        await _broadcast_news(news)
                        await Cache.set(ck, True, ttl=3600)
        except Exception as e:
            logger.error(f"News worker error: {e}")
        await asyncio.sleep(600)


# ════════════════════════════════════════════════════════════════════
# Worker 6: On-Chain (كل ساعة)
# ════════════════════════════════════════════════════════════════════
async def worker_onchain():
    logger.info("⛓️ On-Chain Worker started")
    while True:
        try:
            onchain = await OnChainSource.get_full_onchain()
            await Cache.set(Cache.make_key("onchain", "latest"), onchain, ttl=3600)
        except Exception as e:
            logger.error(f"On-chain worker error: {e}")
        await asyncio.sleep(3600)


# ════════════════════════════════════════════════════════════════════
# Worker 7: Trade Monitor (كل 30 ثانية)
# ════════════════════════════════════════════════════════════════════
async def worker_trade_monitor():
    logger.info("📈 Trade Monitor started")
    while True:
        try:
            from db.client import get_supabase
            sb = get_supabase(service_role=True)
            open_trades = sb.table("trades").select("*").eq("status", "open").execute()
            for trade in (open_trades.data or []):
                await _check_trade(trade)
        except Exception as e:
            logger.error(f"Trade monitor error: {e}")
        await asyncio.sleep(30)


async def _check_trade(trade: dict):
    price_data = await SharedContext.get_price(trade.get("symbol",""))
    if not price_data:
        return
    price = float(price_data.get("price", 0))
    sl    = float(trade.get("stop_loss") or 0)
    tp    = float(trade.get("take_profit") or 0)
    if not price or not sl:
        return

    hit = False
    if trade["direction"] == "long":
        if sl > 0 and price <= sl:   hit = "stop_loss"
        elif tp > 0 and price >= tp: hit = "take_profit"
    else:
        if sl > 0 and price >= sl:   hit = "stop_loss"
        elif tp > 0 and price <= tp: hit = "take_profit"

    if hit:
        await _close_trade(trade, price, hit)


async def _close_trade(trade: dict, exit_price: float, reason: str):
    try:
        from db.client import get_supabase, UserDB
        entry = float(trade["entry_price"])
        qty   = float(trade.get("quantity", 0))
        pnl   = (exit_price - entry) * qty if trade["direction"] == "long" else (entry - exit_price) * qty

        sb = get_supabase(service_role=True)
        sb.table("trades").update({
            "status":     "closed",
            "exit_price": exit_price,
            "pnl_usd":    round(pnl, 2),
            "close_reason": reason
        }).eq("id", trade["id"]).execute()

        user = UserDB.get_by_id(trade["user_id"])
        if user and user.get("telegram_chat_id"):
            from telegram_bot import notify_trade_closed
            await notify_trade_closed(user["telegram_chat_id"], {
                **trade, "pnl_usd": round(pnl, 2), "close_reason": reason
            })
    except Exception as e:
        logger.error(f"Close trade error: {e}")


# ════════════════════════════════════════════════════════════════════
# Broadcast Helpers
# ════════════════════════════════════════════════════════════════════
async def _broadcast_signal(symbol: str, signal: dict):
    try:
        from db.client import get_supabase, UserDB
        sb = get_supabase(service_role=True)
        settings_rows = sb.table("user_settings").select("user_id").eq("notify_signals", True).execute()

        for row in (settings_rows.data or []):
            user = UserDB.get_by_id(row["user_id"])
            if not user or user.get("status") != "active":
                continue
            if user.get("telegram_chat_id"):
                from telegram_bot import notify_signal
                await notify_signal(user["telegram_chat_id"], {
                    "id":            "live",
                    "symbol":         symbol,
                    "direction":      signal["direction"],
                    "entry_price":    signal["entry"],
                    "stop_loss":      signal["stop_loss"],
                    "take_profit_1":  signal["take_profit"],
                    "confidence":     signal["confidence"],
                    "risk_reward":    signal["risk_reward"],
                })
    except Exception as e:
        logger.error(f"Broadcast signal error: {e}")


async def _broadcast_news(news: dict):
    try:
        from db.client import get_supabase, UserDB
        from telegram_bot import send
        sb = get_supabase(service_role=True)
        settings_rows = sb.table("user_settings").select("user_id").eq("notify_news", True).execute()
        emoji = "🟢" if news.get("sentiment") == "bullish" else "🔴"

        for row in (settings_rows.data or []):
            user = UserDB.get_by_id(row["user_id"])
            if user and user.get("telegram_chat_id"):
                await send(user["telegram_chat_id"],
                    f"{emoji} <b>News Alert</b>\n\n"
                    f"{news.get('title','')}\n\n"
                    f"<a href='{news.get('url','')}'>Read more →</a>"
                )
    except Exception as e:
        logger.error(f"Broadcast news error: {e}")


# ════════════════════════════════════════════════════════════════════
# Start All Workers
# ════════════════════════════════════════════════════════════════════
async def start_workers():
    logger.info("🚀 Starting all TradoAI workers...")
    await asyncio.gather(
        worker_websocket(),
        worker_market_scanner(),
        worker_data_refresh(),
        worker_market_report(),
        worker_news(),
        worker_onchain(),
        worker_trade_monitor(),
        return_exceptions=True
    )


if __name__ == "__main__":
    asyncio.run(start_workers())
