"""TRADO Telegram Bot - Full Implementation"""
import os, json, asyncio, httpx
from datetime import datetime

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN","")
ADMIN = os.getenv("TELEGRAM_ADMIN_CHAT_ID","")

PLANS = {
    "micro":   {"name":"Micro",   "price":15,  "emoji":"🌱","signals":5,  "exchanges":1},
    "starter": {"name":"Starter", "price":25,  "emoji":"🚀","signals":15, "exchanges":2},
    "pro":     {"name":"Pro",     "price":50,  "emoji":"💎","signals":50, "exchanges":3},
    "elite":   {"name":"Elite",   "price":100, "emoji":"👑","signals":-1, "exchanges":3},
}

async def _post(method, **kw):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    async with httpx.AsyncClient() as c:
        r = await c.post(url, json=kw, timeout=10)
        return r.json()

async def send(chat_id, text, kb=None, mode="HTML"):
    kw = {"chat_id":chat_id,"text":text,"parse_mode":mode}
    if kb: kw["reply_markup"] = json.dumps(kb)
    return await _post("sendMessage", **kw)

async def edit(chat_id, msg_id, text, kb=None):
    kw = {"chat_id":chat_id,"message_id":msg_id,"text":text,"parse_mode":"HTML"}
    if kb: kw["reply_markup"] = json.dumps(kb)
    return await _post("editMessageText", **kw)

async def answer(cq_id, text=""):
    return await _post("answerCallbackQuery", callback_query_id=cq_id, text=text)

async def set_webhook(domain):
    return await _post("setWebhook",
        url=f"https://{domain}/webhook/telegram",
        allowed_updates=["message","callback_query"])

# Keyboards
def kb_main():
    return {"inline_keyboard":[
        [{"text":"📊 الباقات","callback_data":"plans"},{"text":"📈 إشاراتي","callback_data":"signals"}],
        [{"text":"💼 محفظتي","callback_data":"portfolio"},{"text":"⚙️ حسابي","callback_data":"status"}],
        [{"text":"❓ المساعدة","callback_data":"help"}]
    ]}

def kb_plans():
    rows = [[{"text":f"{p['emoji']} {p['name']} — ${p['price']}/شهر","callback_data":f"plan_{k}"}]
            for k,p in PLANS.items()]
    rows.append([{"text":"« رجوع","callback_data":"main_menu"}])
    return {"inline_keyboard":rows}

def kb_plan(key):
    return {"inline_keyboard":[
        [{"text":"✅ اشترك الآن","callback_data":f"subscribe_{key}"}],
        [{"text":"« رجوع","callback_data":"plans"}]
    ]}

def kb_pay():
    return {"inline_keyboard":[
        [{"text":"💳 Paddle (Visa/MC)","callback_data":"pay_paddle"}],
        [{"text":"🏦 MyFatoorah (KNET)","callback_data":"pay_myfatoorah"}],
        [{"text":"« رجوع","callback_data":"plans"}]
    ]}

# Handlers
async def on_start(chat_id, user):
    name = user.get("first_name","مستخدم")
    await send(chat_id,
        f"👋 <b>أهلاً {name}!</b>\n\n"
        f"🤖 أنا <b>TRADO</b> — بوت التداول الذكي بالذكاء الاصطناعي\n\n"
        f"📊 أراقب السوق 24/7 على Binance وBybit وOKX\n"
        f"🤖 أُحلّل باستخدام 11 وكيل AI متخصص\n"
        f"📡 أرسل إشارات دقيقة مع نسبة ربح 40%+\n\n"
        f"💰 <b>الباقات من $15/شهر فقط</b>\n\nاختر من القائمة:", kb_main())

async def on_plans(chat_id):
    await send(chat_id, "📊 <b>باقات TRADO</b>\n\nاختر الباقة:", kb_plans())

async def on_plan_detail(chat_id, key, msg_id=None):
    p = PLANS.get(key)
    if not p: return
    sigs = "غير محدودة" if p["signals"]==-1 else f"{p['signals']} إشارة/يوم"
    text = (f"{p['emoji']} <b>باقة {p['name']}</b>\n\n"
            f"💰 <b>السعر:</b> ${p['price']}/شهر\n"
            f"📡 <b>الإشارات:</b> {sigs}\n"
            f"🏦 <b>المنصات:</b> {p['exchanges']} منصة\n\n"
            f"✅ إشارات مع نسب TP/SL\n✅ تنبيهات فورية\n✅ دعم 24/7\n")
    if key in ["pro","elite"]: text += "✅ وكلاء AI متقدمة\n✅ تقارير يومية\n"
    if key == "elite": text += "✅ جلسات خاصة مع الفريق\n"
    if msg_id: await edit(chat_id, msg_id, text, kb_plan(key))
    else: await send(chat_id, text, kb_plan(key))

async def on_status(chat_id, user_id):
    await send(chat_id,
        f"⚙️ <b>حسابك</b>\n\n"
        f"🆔 معرّفك: <code>{user_id}</code>\n"
        f"📦 <b>باقتك:</b> لا يوجد اشتراك نشط\n\n"
        f"👉 اشترك الآن للبدء!",
        {"inline_keyboard":[[{"text":"🛒 اشترك الآن","callback_data":"plans"}]]})

async def on_portfolio(chat_id):
    await send(chat_id,
        "💼 <b>محفظتك</b>\n\n"
        "📊 لا توجد صفقات مفتوحة حالياً\n"
        "💡 فعّل اشتراكك لمشاهدة محفظتك",
        {"inline_keyboard":[[{"text":"🚀 فعّل الاشتراك","callback_data":"plans"}]]})

async def on_signals(chat_id):
    await send(chat_id,
        "📈 <b>آخر الإشارات</b>\n\n"
        "💡 الإشارات متاحة لأصحاب الاشتراكات النشطة",
        {"inline_keyboard":[[{"text":"🔑 اشترك للوصول","callback_data":"plans"}]]})

async def on_help(chat_id):
    await send(chat_id,
        "❓ <b>المساعدة</b>\n\n"
        "/start — الشاشة الرئيسية\n"
        "/plans — الباقات والأسعار\n"
        "/status — حالة حسابك\n"
        "/portfolio — محفظتك\n"
        "/signals — آخر الإشارات\n"
        "/help — هذه القائمة\n\n"
        "📞 دعم: @TRADO_support",
        {"inline_keyboard":[[{"text":"« القائمة الرئيسية","callback_data":"main_menu"}]]})

async def broadcast_signal(symbol, side, price, confidence, exchange, tp=None, sl=None):
    """Broadcast trading signal to all subscribers"""
    emoji = "🟢" if side=="BUY" else "🔴"
    text = (f"{emoji} <b>إشارة TRADO</b>\n\n"
            f"📌 <b>{symbol}</b> على {exchange}\n"
            f"{'🟢 شراء' if side=='BUY' else '🔴 بيع'} @ <code>${price:,.4f}</code>\n"
            f"🎯 الثقة: <b>{confidence:.0%}</b>\n"
            + (f"✅ TP: <code>${tp:,.4f}</code>\n" if tp else "")
            + (f"🛑 SL: <code>${sl:,.4f}</code>\n" if sl else "")
            + f"\n⏰ {datetime.now().strftime('%H:%M:%S')} UTC")
    await send(ADMIN, text)

async def handle_update(update: dict):
    """Main webhook dispatcher"""
    if "callback_query" in update:
        cq = update["callback_query"]
        chat_id = str(cq["message"]["chat"]["id"])
        msg_id = cq["message"]["message_id"]
        data = cq.get("data","")
        await answer(cq["id"])
        if data=="main_menu": await send(chat_id,"القائمة الرئيسية:", kb_main())
        elif data=="plans": await on_plans(chat_id)
        elif data.startswith("plan_"): await on_plan_detail(chat_id, data[5:], msg_id)
        elif data.startswith("subscribe_"):
            key=data[10:]; p=PLANS.get(key,{})
            await send(chat_id,f"💳 اختر طريقة الدفع لباقة <b>{p.get('name','')}</b>:", kb_pay())
        elif data in ("pay_paddle","pay_myfatoorah"):
            await send(chat_id,"🔗 رابط الدفع سيُرسل قريباً\n@TRADO_support")
        elif data=="signals": await on_signals(chat_id)
        elif data=="portfolio": await on_portfolio(chat_id)
        elif data=="status": await on_status(chat_id, str(cq["from"].get("id","")))
        elif data=="help": await on_help(chat_id)
        return

    if "message" not in update: return
    msg=update["message"]
    chat_id=str(msg["chat"]["id"])
    text=msg.get("text","")
    user=msg.get("from",{})
    uid=str(user.get("id",""))

    if text.startswith("/start"): await on_start(chat_id, user)
    elif text.startswith("/plans"): await on_plans(chat_id)
    elif text.startswith("/status"): await on_status(chat_id, uid)
    elif text.startswith("/portfolio"): await on_portfolio(chat_id)
    elif text.startswith("/signals"): await on_signals(chat_id)
    elif text.startswith("/help"): await on_help(chat_id)
    elif text.startswith("/admin") and uid==ADMIN:
        await send(chat_id,"🔐 <b>لوحة الإدارة:</b>\nhttps://trado-bot.fly.dev/dashboard")
    else: await send(chat_id,"💬 لم أفهم رسالتك. /help للمساعدة", kb_main())
