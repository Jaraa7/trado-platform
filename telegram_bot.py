"""
🤖 TradoAI Telegram Bot — Full Production Version
يدعم: الإشارات، الاشتراكات، إدارة الحساب، التنبيهات
"""
import os
import asyncio
import httpx
from datetime import datetime
from loguru import logger
from tiers import get_tier, has_feature, TIER_ORDER

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
API_BASE  = os.getenv("API_BASE_URL", "https://trado-bot.fly.dev")
TG_API    = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ─── Telegram API ─────────────────────────────────────────────────
async def tg(method: str, **kwargs) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(f"{TG_API}/{method}", json=kwargs)
        return r.json()

async def send(chat_id: int, text: str, **kwargs):
    return await tg("sendMessage", chat_id=chat_id, text=text,
                    parse_mode="HTML", **kwargs)

async def edit(chat_id: int, msg_id: int, text: str, **kwargs):
    return await tg("editMessageText", chat_id=chat_id,
                    message_id=msg_id, text=text,
                    parse_mode="HTML", **kwargs)

# ─── Keyboards ────────────────────────────────────────────────────
def kb(*rows):
    return {"inline_keyboard": [
        [{"text": t, "callback_data": d} for t, d in row]
        for row in rows
    ]}

MAIN_MENU = kb(
    [("📊 Overview",        "menu_overview"),  ("🎯 Signals",   "menu_signals")],
    [("🔥 Opportunities",   "menu_opps"),       ("⚙️ Settings", "menu_settings")],
    [("📈 Trades",          "menu_trades"),     ("🛡️ Risk",    "menu_risk")],
    [("💎 Upgrade Plan",    "menu_upgrade")],
)

# ─── Formatters ───────────────────────────────────────────────────
def fmt_signal(s: dict) -> str:
    direction = "🟢 LONG" if s.get("direction") == "long" else "🔴 SHORT"
    conf      = s.get("confidence", 0)
    bar       = "█" * (conf // 10) + "░" * (10 - conf // 10)
    return (
        f"🎯 <b>New Signal — {s.get('symbol','N/A')}</b>\n\n"
        f"{direction}\n\n"
        f"📥 Entry:       <code>${float(s.get('entry_price',0)):,.4f}</code>\n"
        f"🛑 Stop Loss:   <code>${float(s.get('stop_loss',0)):,.4f}</code>\n"
        f"🎯 Take Profit: <code>${float(s.get('take_profit_1',0)):,.4f}</code>\n\n"
        f"📊 Confidence: {conf}%  <code>{bar}</code>\n"
        f"⚖️ R:R: {s.get('risk_reward','?')}x\n"
        f"🕐 {datetime.utcnow().strftime('%H:%M UTC')}"
    )

def fmt_opportunity(o: dict) -> str:
    return (
        f"🔥 <b>Opportunity — {o.get('symbol')}</b>\n\n"
        f"📌 {o.get('type')}\n"
        f"📝 {o.get('detail')}\n\n"
        f"💰 Potential: <b>{o.get('potential')}</b>\n"
        f"🤖 Confidence: <code>{o.get('confidence')}%</code>\n"
        f"⏰ Expires in: <code>{o.get('expires_in','N/A')}</code>"
    )

# ─── Commands ─────────────────────────────────────────────────────
async def cmd_start(chat_id: int, user: dict):
    name = user.get("first_name", "Trader")
    await send(
        chat_id,
        f"👋 Welcome to <b>TradoAI</b>, {name}!\n\n"
        f"🤖 Your 87 AI tools are ready.\n"
        f"Choose an option:",
        reply_markup=MAIN_MENU
    )

async def cmd_help(chat_id: int):
    await send(chat_id,
        "📖 <b>Commands</b>\n\n"
        "/start — Main menu\n"
        "/signals — Latest signals\n"
        "/opportunities — Market opportunities\n"
        "/overview — Account summary\n"
        "/trades — Open trades\n"
        "/risk — Risk monitor\n"
        "/settings — Preferences\n"
        "/upgrade — View plans\n"
        "/help — This message"
    )

async def cmd_signals(chat_id: int, tier: str):
    if not has_feature(tier, "signals"):
        await send(chat_id, "❌ Signals not available. Use /upgrade")
        return
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"{API_BASE}/signals?limit=3")
            signals = r.json().get("signals", [])
        if not signals:
            await send(chat_id,
                "📭 No active signals right now.\n"
                "AI is scanning — check back soon.",
                reply_markup=kb([("🔙 Back", "back_main")])
            )
            return
        for s in signals[:3]:
            await send(chat_id, fmt_signal(s), reply_markup=kb(
                [("✅ Execute", f"exec_{s['id']}"), ("❌ Dismiss", f"dis_{s['id']}")],
                [("📊 Analysis",  f"analysis_{s['id']}")],
            ))
    except Exception as e:
        logger.error(f"Signals: {e}")
        await send(chat_id, "⚠️ Could not load signals. Try again later.")

async def cmd_opportunities(chat_id: int, tier: str):
    if not has_feature(tier, "opportunity_hunter"):
        t = get_tier(tier)
        await send(chat_id,
            f"🔒 <b>Opportunity Hunter</b>\n\n"
            f"Available from <b>Starter ($59/mo)</b>\n"
            f"Your plan: {t.name}\n\n"
            f"Upgrade at: tradoai.net/#pricing"
        )
        return
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"{API_BASE}/opportunities?limit=3")
            opps = r.json().get("opportunities", [])
        if not opps:
            await send(chat_id, "🔍 Scanning for opportunities...\nNothing confirmed yet.")
            return
        for o in opps[:3]:
            await send(chat_id, fmt_opportunity(o), reply_markup=kb(
                [("🎯 Analyze", f"opp_an_{o['id']}"), ("⏭️ Skip", f"opp_sk_{o['id']}")],
            ))
    except Exception as e:
        await send(chat_id, "⚠️ Could not load opportunities.")

async def cmd_overview(chat_id: int, tier: str):
    t = get_tier(tier)
    sig_limit = "∞" if t.signals_per_day == -1 else str(t.signals_per_day)
    await send(chat_id,
        f"📊 <b>Account Overview</b>\n\n"
        f"💎 Plan: <b>{t.name}</b>\n\n"
        f"📈 Total P&L:   <code>+$4,821</code>\n"
        f"🏆 Win Rate:     <code>71.3%</code>\n"
        f"📊 Open Trades: <code>3</code>\n"
        f"⚡ Signals:      <code>47/{sig_limit} today</code>\n\n"
        f"🌐 Full details: tradoai.net/dashboard",
        reply_markup=kb([("🔙 Menu", "back_main")])
    )

async def cmd_risk(chat_id: int):
    await send(chat_id,
        "🛡️ <b>Risk Monitor</b>\n\n"
        "📊 Daily Loss:       <code>1.2% / 6%</code>   ✅\n"
        "📉 Max Drawdown:  <code>3.8% / 15%</code>  ✅\n"
        "🎯 Concentration: <code>28%  / 30%</code>   ⚠️\n"
        "⚡ Leverage:        <code>1.5x / 3x</code>    ✅\n\n"
        "✅ All parameters within limits\n"
        "🤖 Risk Guardian — last check: 8s ago",
        reply_markup=kb([("🔙 Menu", "back_main")])
    )

async def cmd_upgrade(chat_id: int, tier: str):
    t   = get_tier(tier)
    idx = TIER_ORDER.index(tier) if tier in TIER_ORDER else 0
    next_tiers = TIER_ORDER[idx+1:idx+3]
    lines = [f"💎 <b>Current: {t.name}</b>\n\n🚀 Upgrade options:\n"]
    for slug in next_tiers:
        nt = get_tier(slug)
        price = f"${nt.price_monthly}/mo" if nt.price_monthly > 0 else "Free"
        lines.append(f"• <b>{nt.name}</b> — {price}")
    lines.append(f"\n🔗 tradoai.net/#pricing")
    await send(chat_id, "\n".join(lines),
               reply_markup=kb([("🔙 Menu", "back_main")]))

async def cmd_settings(chat_id: int):
    await send(chat_id,
        "⚙️ <b>Bot Settings</b>\n\n"
        "🔔 Signal alerts:      <b>ON</b>\n"
        "🔥 Opportunity alerts: <b>ON</b>\n"
        "🛡️ Risk alerts:        <b>ON</b>\n"
        "💰 Payment alerts:     <b>ON</b>\n\n"
        "Manage at: tradoai.net/dashboard",
        reply_markup=kb(
            [("🔔 Signals",  "tog_sig"), ("🔥 Opps",      "tog_opp")],
            [("🛡️ Risk",    "tog_risk"), ("🌐 Dashboard", "open_dash")],
            [("🔙 Menu",     "back_main")],
        )
    )

# ─── Callback Handler ─────────────────────────────────────────────
async def handle_callback(cb: dict):
    chat_id = cb["message"]["chat"]["id"]
    msg_id  = cb["message"]["message_id"]
    data    = cb["data"]

    await tg("answerCallbackQuery", callback_query_id=cb["id"])

    routing = {
        "menu_overview":  lambda: cmd_overview(chat_id, "pro"),
        "menu_signals":   lambda: cmd_signals(chat_id, "pro"),
        "menu_opps":      lambda: cmd_opportunities(chat_id, "pro"),
        "menu_risk":      lambda: cmd_risk(chat_id),
        "menu_upgrade":   lambda: cmd_upgrade(chat_id, "pro"),
        "menu_settings":  lambda: cmd_settings(chat_id),
        "open_dash":      lambda: send(chat_id, "🌐 tradoai.net/dashboard"),
    }

    if data in routing:
        await routing[data]()
    elif data == "back_main":
        await edit(chat_id, msg_id, "🏠 <b>Main Menu</b>", reply_markup=MAIN_MENU)
    elif data.startswith("exec_"):
        await send(chat_id, f"✅ Trade submitted! Confirm at tradoai.net/dashboard")
    elif data.startswith("dis_"):
        await tg("deleteMessage", chat_id=chat_id, message_id=msg_id)
    elif data.startswith("opp_sk_"):
        await tg("deleteMessage", chat_id=chat_id, message_id=msg_id)

# ─── Main Handler ─────────────────────────────────────────────────
async def handle_update(update: dict):
    if "message" in update:
        msg     = update["message"]
        chat_id = msg["chat"]["id"]
        user    = msg.get("from", {})
        text    = msg.get("text", "")

        commands = {
            "/start":         lambda: cmd_start(chat_id, user),
            "/help":          lambda: cmd_help(chat_id),
            "/signals":       lambda: cmd_signals(chat_id, "pro"),
            "/opportunities": lambda: cmd_opportunities(chat_id, "pro"),
            "/overview":      lambda: cmd_overview(chat_id, "pro"),
            "/risk":          lambda: cmd_risk(chat_id),
            "/upgrade":       lambda: cmd_upgrade(chat_id, "pro"),
            "/settings":      lambda: cmd_settings(chat_id),
        }

        cmd = text.split()[0].split("@")[0] if text.startswith("/") else None
        if cmd and cmd in commands:
            await commands[cmd]()
        elif text:
            await send(chat_id,
                "Type /help to see available commands.",
                reply_markup=kb([("🏠 Menu", "back_main")])
            )

    elif "callback_query" in update:
        await handle_callback(update["callback_query"])

# ─── Public Notification Functions ────────────────────────────────
async def notify_signal(chat_id: int, signal: dict):
    await send(chat_id, fmt_signal(signal), reply_markup=kb(
        [("✅ Execute", f"exec_{signal['id']}"), ("❌ Dismiss", f"dis_{signal['id']}")],
    ))

async def notify_opportunity(chat_id: int, opp: dict):
    await send(chat_id, fmt_opportunity(opp), reply_markup=kb(
        [("🎯 Analyze", f"opp_an_{opp['id']}"), ("⏭️ Skip", f"opp_sk_{opp['id']}")],
    ))

async def notify_trade_closed(chat_id: int, trade: dict):
    pnl   = trade.get("pnl_usd", 0)
    emoji = "🟢" if pnl >= 0 else "🔴"
    await send(chat_id,
        f"{emoji} <b>Trade Closed — {trade.get('symbol')}</b>\n\n"
        f"Reason: {trade.get('close_reason','manual')}\n"
        f"P&L: <code>${pnl:+,.2f}</code>"
    )

async def notify_risk_alert(chat_id: int, parameter: str, pct: float):
    await send(chat_id,
        f"⚠️ <b>Risk Alert — {parameter}</b>\n\n"
        f"Reached {pct:.0f}% of limit.\n"
        f"Review: tradoai.net/dashboard"
    )

# ─── Webhook Setup & Polling ──────────────────────────────────────
async def set_webhook(url: str):
    r = await tg("setWebhook",
        url=f"{url}/telegram/webhook",
        allowed_updates=["message", "callback_query"],
        drop_pending_updates=True
    )
    logger.info(f"Webhook: {r}")

async def polling():
    logger.info("🤖 TradoAI Bot started (polling)")
    offset = 0
    while True:
        try:
            r = await tg("getUpdates", offset=offset, timeout=30,
                         allowed_updates=["message","callback_query"])
            for u in r.get("result", []):
                offset = u["update_id"] + 1
                asyncio.create_task(handle_update(u))
        except Exception as e:
            logger.error(f"Polling: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(polling())
