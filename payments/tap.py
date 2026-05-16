"""
💳 TradoAI — Tap Payments Integration
نظام دفع كامل مع Tap Payments

يدعم:
- One-time charges (دفع مرة واحدة)
- Subscriptions (اشتراكات متكررة)
- Webhooks (تحديثات تلقائية)
- KNET + بطاقات + Apple Pay
"""
import os
import hmac
import hashlib
import httpx
from datetime import datetime
from loguru import logger
from tiers import TIERS, get_tier, TIER_ORDER

TAP_SECRET_KEY = os.getenv("TAP_SECRET_KEY", "")   # sk_live_...
TAP_PUBLIC_KEY = os.getenv("TAP_PUBLIC_KEY", "")   # pk_live_...
TAP_BASE       = "https://api.tap.company/v2"
FRONTEND_URL   = os.getenv("FRONTEND_URL", "https://trado-platform.vercel.app")


# ─── HTTP Client ──────────────────────────────────────────────────
async def _tap(method: str, endpoint: str, data: dict = None) -> dict:
    headers = {
        "Authorization": f"Bearer {TAP_SECRET_KEY}",
        "Content-Type":  "application/json",
    }
    async with httpx.AsyncClient(timeout=15) as c:
        if method == "POST":
            r = await c.post(f"{TAP_BASE}{endpoint}", json=data, headers=headers)
        elif method == "GET":
            r = await c.get(f"{TAP_BASE}{endpoint}", headers=headers)
        else:
            r = await c.put(f"{TAP_BASE}{endpoint}", json=data, headers=headers)
        return r.json()


# ════════════════════════════════════════════════════════════════════
# 1. CHARGES (دفع مرة واحدة)
# ════════════════════════════════════════════════════════════════════

async def create_charge(
    amount: float,
    currency: str = "USD",
    customer_email: str = "",
    customer_name: str = "",
    description: str = "",
    metadata: dict = None,
    redirect_url: str = None,
) -> dict:
    """إنشاء charge جديد"""
    payload = {
        "amount": amount,
        "currency": currency,
        "customer": {
            "email":      customer_email,
            "first_name": customer_name.split()[0] if customer_name else "",
            "last_name":  " ".join(customer_name.split()[1:]) if len(customer_name.split()) > 1 else "",
        },
        "source": {"id": "src_all"},  # كل طرق الدفع
        "redirect": {
            "url": redirect_url or f"{FRONTEND_URL}/checkout/success"
        },
        "description": description,
        "metadata": metadata or {},
        "reference": {
            "transaction": f"TRD-{int(datetime.utcnow().timestamp())}",
            "order":       f"ORD-{int(datetime.utcnow().timestamp())}",
        },
    }
    result = await _tap("POST", "/charges", payload)
    logger.info(f"Charge created: {result.get('id')} status={result.get('status')}")
    return result


# ════════════════════════════════════════════════════════════════════
# 2. SUBSCRIPTIONS (اشتراكات متكررة)
# ════════════════════════════════════════════════════════════════════

# خريطة الباقات لـ Tap Plans
BILLING_PERIOD = {
    "monthly": {"period": "MONTH", "frequency": 1},
    "annual":  {"period": "YEAR",  "frequency": 1},
}

async def create_plan(tier_slug: str, billing: str = "monthly") -> dict:
    """إنشاء Plan في Tap لباقة معينة"""
    tier  = get_tier(tier_slug)
    price = tier.price_monthly if billing == "monthly" else (tier.price_annual or tier.price_monthly * 12)
    freq  = BILLING_PERIOD.get(billing, BILLING_PERIOD["monthly"])

    payload = {
        "name":        f"TradoAI {tier.name} - {billing.capitalize()}",
        "amount":      price,
        "currency":    "USD",
        "interval":    freq,
        "metadata":    {"tier": tier_slug, "billing": billing},
        "trial": {
            "days": 7 if tier_slug == "trial" else 0
        } if tier_slug == "trial" else {},
    }
    result = await _tap("POST", "/plans", payload)
    logger.info(f"Plan created: {result.get('id')} for {tier_slug}/{billing}")
    return result


async def create_subscription(
    plan_id: str,
    customer_email: str,
    customer_name: str,
    tier_slug: str,
    user_id: str,
    billing: str = "monthly",
) -> dict:
    """إنشاء اشتراك جديد"""
    payload = {
        "plan": {"id": plan_id},
        "customer": {
            "email":      customer_email,
            "first_name": customer_name.split()[0] if customer_name else "",
            "last_name":  " ".join(customer_name.split()[1:]) if len(customer_name.split()) > 1 else "",
        },
        "source":   {"id": "src_all"},
        "redirect": {"url": f"{FRONTEND_URL}/checkout/success?tier={tier_slug}"},
        "metadata": {
            "user_id":   user_id,
            "tier":      tier_slug,
            "billing":   billing,
        },
        "auto_renewal": True,
    }
    result = await _tap("POST", "/subscriptions", payload)
    logger.info(f"Subscription: {result.get('id')} for user {user_id} tier={tier_slug}")
    return result


async def cancel_subscription(subscription_id: str) -> dict:
    """إلغاء اشتراك"""
    result = await _tap("PUT", f"/subscriptions/{subscription_id}", {"status": "CANCELLED"})
    logger.info(f"Subscription cancelled: {subscription_id}")
    return result


async def get_subscription(subscription_id: str) -> dict:
    return await _tap("GET", f"/subscriptions/{subscription_id}")


# ════════════════════════════════════════════════════════════════════
# 3. CUSTOMERS
# ════════════════════════════════════════════════════════════════════

async def create_customer(email: str, name: str, phone: str = "") -> dict:
    payload = {
        "email":      email,
        "first_name": name.split()[0] if name else "",
        "last_name":  " ".join(name.split()[1:]) if len(name.split()) > 1 else "",
        "phone": {"country_code": "965", "number": phone} if phone else {},
    }
    return await _tap("POST", "/customers", payload)


async def get_customer(customer_id: str) -> dict:
    return await _tap("GET", f"/customers/{customer_id}")


# ════════════════════════════════════════════════════════════════════
# 4. WEBHOOKS
# ════════════════════════════════════════════════════════════════════

def verify_webhook(payload: bytes, signature: str) -> bool:
    """التحقق من صحة webhook من Tap"""
    expected = hmac.new(
        TAP_SECRET_KEY.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


async def handle_webhook(event: dict, db) -> dict:
    """معالجة webhook events من Tap"""
    event_type = event.get("object", "")
    logger.info(f"Tap webhook: {event_type} id={event.get('id')}")

    # ── Charge events ────────────────────────────────────────────
    if event_type == "charge":
        status = event.get("status", "")
        meta   = event.get("metadata", {})
        user_id= meta.get("user_id")

        if status == "CAPTURED":
            await _on_payment_success(event, db)
        elif status in ["CANCELLED", "FAILED", "DECLINED"]:
            await _on_payment_failed(event, db)

    # ── Subscription events ───────────────────────────────────────
    elif event_type == "subscription":
        status = event.get("status", "")
        meta   = event.get("metadata", {})

        if status == "ACTIVE":
            await _on_subscription_activated(event, db)
        elif status == "CANCELLED":
            await _on_subscription_cancelled(event, db)
        elif status == "PAST_DUE":
            await _on_payment_failed(event, db)

    return {"received": True}


async def _on_payment_success(event: dict, db):
    meta    = event.get("metadata", {})
    user_id = meta.get("user_id")
    tier    = meta.get("tier", "micro")
    billing = meta.get("billing", "monthly")
    amount  = event.get("amount", 0)

    if not user_id:
        return

    # حدّث subscription في DB
    from db.client import get_supabase
    sb = get_supabase(service_role=True)

    t       = get_tier(tier)
    end_date= _calc_end_date(billing)

    sb.table("subscriptions").upsert({
        "user_id":         user_id,
        "tier":            tier,
        "status":          "active",
        "billing_cycle":   billing,
        "current_period_end": end_date,
        "tap_subscription_id": event.get("id"),
    }).execute()

    sb.table("payments").insert({
        "user_id":     user_id,
        "amount":      amount,
        "currency":    event.get("currency", "USD"),
        "status":      "completed",
        "gateway":     "tap",
        "gateway_id":  event.get("id"),
        "tier":        tier,
    }).execute()

    # أرسل إشعار Telegram
    from db.client import UserDB
    user = UserDB.get_by_id(user_id)
    if user and user.get("telegram_chat_id"):
        from telegram_bot import send
        await send(user["telegram_chat_id"],
            f"✅ <b>Payment Confirmed!</b>\n\n"
            f"Plan: <b>{t.name}</b>\n"
            f"Amount: <b>${amount}</b>\n"
            f"Your {t.name} features are now active.\n\n"
            f"<a href='{FRONTEND_URL}/dashboard'>Open Dashboard →</a>"
        )

    logger.info(f"✅ Payment success: user={user_id} tier={tier} amount=${amount}")


async def _on_payment_failed(event: dict, db):
    meta    = event.get("metadata", {})
    user_id = meta.get("user_id")
    if not user_id:
        return

    from db.client import get_supabase, UserDB
    sb = get_supabase(service_role=True)
    sb.table("payments").insert({
        "user_id":    user_id,
        "amount":     event.get("amount", 0),
        "status":     "failed",
        "gateway":    "tap",
        "gateway_id": event.get("id"),
    }).execute()

    user = UserDB.get_by_id(user_id)
    if user and user.get("telegram_chat_id"):
        from telegram_bot import send
        await send(user["telegram_chat_id"],
            f"❌ <b>Payment Failed</b>\n\n"
            f"Please update your payment method:\n"
            f"{FRONTEND_URL}/billing"
        )


async def _on_subscription_activated(event: dict, db):
    await _on_payment_success(event, db)


async def _on_subscription_cancelled(event: dict, db):
    meta    = event.get("metadata", {})
    user_id = meta.get("user_id")
    if not user_id:
        return

    from db.client import get_supabase
    sb = get_supabase(service_role=True)
    sb.table("subscriptions").update({
        "status": "cancelled"
    }).eq("user_id", user_id).execute()


def _calc_end_date(billing: str) -> str:
    from datetime import timedelta
    now = datetime.utcnow()
    if billing == "annual":
        return (now.replace(year=now.year + 1)).isoformat()
    return (now.replace(month=now.month + 1) if now.month < 12
            else now.replace(year=now.year + 1, month=1)).isoformat()


# ════════════════════════════════════════════════════════════════════
# 5. CHECKOUT SESSION BUILDER
# يبني URL الدفع لكل باقة
# ════════════════════════════════════════════════════════════════════

async def build_checkout_url(
    tier_slug: str,
    billing: str,
    user_id: str,
    email: str,
    name: str,
) -> dict:
    """يبني رابط الدفع الكامل"""
    tier  = get_tier(tier_slug)
    price = tier.price_monthly if billing == "monthly" else (tier.price_annual or tier.price_monthly * 12)

    charge = await create_charge(
        amount=price,
        currency="USD",
        customer_email=email,
        customer_name=name,
        description=f"TradoAI {tier.name} - {billing.capitalize()}",
        metadata={"user_id": user_id, "tier": tier_slug, "billing": billing},
        redirect_url=f"{FRONTEND_URL}/checkout/success?tier={tier_slug}&billing={billing}",
    )

    return {
        "charge_id":   charge.get("id"),
        "checkout_url":charge.get("transaction", {}).get("url", ""),
        "amount":      price,
        "tier":        tier_slug,
        "billing":     billing,
        "status":      charge.get("status"),
    }
