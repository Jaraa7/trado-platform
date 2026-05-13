import asyncio
import httpx
from datetime import datetime

async def send_telegram(token: str, chat_id: str, message: str):
    """Send message via Telegram Bot API"""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=10)
            return resp.json()
    except Exception as e:
        print(f"[Telegram] Error: {e}")
        return None

async def notify_trade(token, chat_id, symbol, side, price, pnl=None):
    emoji = "" if side == "BUY" else ""
    msg = (f"{emoji} <b>TRADO - {side}</b>\n"
           f"Symbol: <code>{symbol}</code>\n"
           f"Price: <code>${price:,.4f}</code>")
    if pnl is not None:
        p_emoji = "" if pnl >= 0 else ""
        msg += f"\nPnL: <code>{p_emoji}${pnl:+,.2f}</code>"
    await send_telegram(token, chat_id, msg)

async def notify_hard_stop(token, chat_id, balance, loss_pct):
    msg = (f" <b>HARD STOP TRIGGERED</b>\n"
           f"Weekly Loss: <code>{loss_pct:.1f}%</code>\n"
           f"Balance: <code>${balance:,.2f}</code>\n"
           f"Action: All trading stopped")
    await send_telegram(token, chat_id, msg)
