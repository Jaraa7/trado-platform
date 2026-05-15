"""
💳 Lemon Squeezy Payment Integration
يتعامل مع المدفوعات + الاشتراكات + الـ webhooks
"""
import os
import hmac
import hashlib
import httpx
from fastapi import APIRouter, Request, HTTPException, Header, Depends
from loguru import logger
from db.client import get_supabase, UserDB, SubscriptionDB, audit
from auth.service import get_current_user


# ════════════════════════════════════════════════════════════════════
# Configuration
# ════════════════════════════════════════════════════════════════════

LS_API_KEY = os.getenv("LEMONSQUEEZY_API_KEY", "")
LS_STORE_ID = os.getenv("LEMONSQUEEZY_STORE_ID", "")
LS_WEBHOOK_SECRET = os.getenv("LEMONSQUEEZY_WEBHOOK_SECRET", "")
LS_API_BASE = "https://api.lemonsqueezy.com/v1"


# ════════════════════════════════════════════════════════════════════
# Tier → Variant ID Mapping (يتم تعبئته بعد إنشاء المنتجات)
# ════════════════════════════════════════════════════════════════════

TIER_VARIANTS = {
    "micro_monthly":       os.getenv("LS_MICRO_MONTHLY_VARIANT", ""),
    "micro_annual":        os.getenv("LS_MICRO_ANNUAL_VARIANT", ""),
    "starter_monthly":     os.getenv("LS_STARTER_MONTHLY_VARIANT", ""),
    "starter_annual":      os.getenv("LS_STARTER_ANNUAL_VARIANT", ""),
    "pro_monthly":         os.getenv("LS_PRO_MONTHLY_VARIANT", ""),
    "pro_annual":          os.getenv("LS_PRO_ANNUAL_VARIANT", ""),
    "elite_monthly":       os.getenv("LS_ELITE_MONTHLY_VARIANT", ""),
    "elite_annual":        os.getenv("LS_ELITE_ANNUAL_VARIANT", ""),
    "whale_monthly":       os.getenv("LS_WHALE_MONTHLY_VARIANT", ""),
    "whale_annual":        os.getenv("LS_WHALE_ANNUAL_VARIANT", ""),
    "institutional_monthly": os.getenv("LS_INSTITUTIONAL_MONTHLY_VARIANT", ""),
    "founder_monthly":     os.getenv("LS_FOUNDER_MONTHLY_VARIANT", ""),
}


# ════════════════════════════════════════════════════════════════════
# API Client
# ════════════════════════════════════════════════════════════════════

class LemonSqueezyClient:

    @staticmethod
    async def _request(method: str, path: str, **kwargs) -> dict:
        headers = {
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
            "Authorization": f"Bearer {LS_API_KEY}",
        }
        url = f"{LS_API_BASE}{path}"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.request(method, url, headers=headers, **kwargs)
            if resp.status_code >= 400:
                logger.error(f"LS API error: {resp.status_code} {resp.text}")
                raise HTTPException(resp.status_code, "Payment provider error")
            return resp.json()

    @staticmethod
    async def create_checkout(variant_id: str, user_email: str, user_id: str,
                              redirect_url: str = None) -> str:
        """إنشاء checkout URL"""
        payload = {
            "data": {
                "type": "checkouts",
                "attributes": {
                    "checkout_data": {
                        "email": user_email,
                        "custom": {"user_id": user_id},
                    },
                    "product_options": {
                        "redirect_url": redirect_url or "https://tradoai.net/dashboard?checkout=success",
                    },
                },
                "relationships": {
                    "store": {"data": {"type": "stores", "id": LS_STORE_ID}},
                    "variant": {"data": {"type": "variants", "id": variant_id}},
                },
            }
        }
        result = await LemonSqueezyClient._request("POST", "/checkouts", json=payload)
        return result["data"]["attributes"]["url"]

    @staticmethod
    async def get_subscription(sub_id: str) -> dict:
        result = await LemonSqueezyClient._request("GET", f"/subscriptions/{sub_id}")
        return result["data"]

    @staticmethod
    async def cancel_subscription(sub_id: str) -> dict:
        return await LemonSqueezyClient._request("DELETE", f"/subscriptions/{sub_id}")

    @staticmethod
    async def pause_subscription(sub_id: str) -> dict:
        payload = {
            "data": {
                "type": "subscriptions",
                "id": sub_id,
                "attributes": {"pause": {"mode": "void"}},
            }
        }
        return await LemonSqueezyClient._request("PATCH", f"/subscriptions/{sub_id}", json=payload)

    @staticmethod
    async def resume_subscription(sub_id: str) -> dict:
        payload = {
            "data": {
                "type": "subscriptions",
                "id": sub_id,
                "attributes": {"pause": None, "cancelled": False},
            }
        }
        return await LemonSqueezyClient._request("PATCH", f"/subscriptions/{sub_id}", json=payload)

    @staticmethod
    async def update_payment_method(sub_id: str) -> str:
        """جلب رابط لتحديث بطاقة الدفع"""
        result = await LemonSqueezyClient._request("GET", f"/subscriptions/{sub_id}")
        return result["data"]["attributes"]["urls"]["update_payment_method"]


# ════════════════════════════════════════════════════════════════════
# Webhook Handler
# ════════════════════════════════════════════════════════════════════

def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """التحقق من Lemon Squeezy webhook signature"""
    if not LS_WEBHOOK_SECRET:
        return False
    expected = hmac.new(
        LS_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


async def handle_subscription_created(data: dict):
    """عند إنشاء اشتراك جديد"""
    attrs = data["attributes"]
    user_id = attrs.get("custom_data", {}).get("user_id")
    if not user_id:
        logger.error("No user_id in subscription_created webhook")
        return

    variant_id = str(attrs["variant_id"])
    tier = _variant_to_tier(variant_id)

    SubscriptionDB.create(
        user_id=user_id,
        tier=tier,
        amount=float(attrs["amount"] or 0) / 100,    # cents to dollars
        billing_cycle=_get_billing_cycle(variant_id),
        ls_subscription_id=str(data["id"]),
        ls_customer_id=str(attrs.get("customer_id", "")),
        ls_variant_id=variant_id,
        current_period_start=attrs.get("current_period_start"),
        current_period_end=attrs.get("renews_at"),
    )

    audit(user_id, "subscription_created", "subscription", str(data["id"]),
          metadata={"tier": tier, "amount": attrs["amount"]})

    logger.info(f"✅ New subscription: user={user_id[:8]} tier={tier}")


async def handle_subscription_updated(data: dict):
    """عند تحديث اشتراك"""
    sb = get_supabase(service_role=True)
    sub_id = str(data["id"])
    attrs = data["attributes"]

    sb.table("subscriptions").update({
        "status": "active" if not attrs.get("cancelled") else "cancelled",
        "current_period_end": attrs.get("renews_at"),
    }).eq("ls_subscription_id", sub_id).execute()

    logger.info(f"Subscription updated: {sub_id}")


async def handle_payment_success(data: dict):
    """عند نجاح دفع"""
    attrs = data["attributes"]
    user_id = attrs.get("custom_data", {}).get("user_id")
    if not user_id:
        return

    sb = get_supabase(service_role=True)
    sb.table("payments").insert({
        "user_id": user_id,
        "amount": float(attrs.get("total", 0)) / 100,
        "subtotal": float(attrs.get("subtotal", 0)) / 100,
        "tax_amount": float(attrs.get("tax", 0)) / 100,
        "currency": attrs.get("currency", "USD"),
        "provider": "lemon_squeezy",
        "provider_payment_id": str(data["id"]),
        "provider_invoice_url": attrs.get("urls", {}).get("invoice_url"),
        "status": "succeeded",
        "paid_at": attrs.get("created_at"),
    }).execute()

    audit(user_id, "payment_success", "payment", str(data["id"]),
          metadata={"amount": attrs.get("total")})


async def handle_payment_failed(data: dict):
    """عند فشل دفع"""
    attrs = data["attributes"]
    user_id = attrs.get("custom_data", {}).get("user_id")
    if not user_id:
        return

    sb = get_supabase(service_role=True)
    sb.table("payments").insert({
        "user_id": user_id,
        "amount": float(attrs.get("total", 0)) / 100,
        "provider": "lemon_squeezy",
        "provider_payment_id": str(data["id"]),
        "status": "failed",
        "failure_reason": attrs.get("status_formatted"),
    }).execute()

    # TODO: trigger Failed Payment Recovery agent
    logger.warning(f"Payment failed: user={user_id[:8]}")


# ════════════════════════════════════════════════════════════════════
# Helper Functions
# ════════════════════════════════════════════════════════════════════

def _variant_to_tier(variant_id: str) -> str:
    """تحويل variant ID إلى tier name"""
    for key, vid in TIER_VARIANTS.items():
        if vid == variant_id:
            return key.split("_")[0]    # "pro_monthly" → "pro"
    return "unknown"


def _get_billing_cycle(variant_id: str) -> str:
    for key, vid in TIER_VARIANTS.items():
        if vid == variant_id:
            return "annual" if "annual" in key else "monthly"
    return "monthly"


# ════════════════════════════════════════════════════════════════════
# Routes
# ════════════════════════════════════════════════════════════════════

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/checkout")
async def create_checkout(
    tier: str,
    billing: str = "monthly",
    user: dict = Depends(get_current_user)
):
    """إنشاء جلسة checkout"""
    variant_key = f"{tier}_{billing}"
    variant_id = TIER_VARIANTS.get(variant_key)
    if not variant_id:
        raise HTTPException(400, f"Plan not available: {variant_key}")

    checkout_url = await LemonSqueezyClient.create_checkout(
        variant_id=variant_id,
        user_email=user["email"],
        user_id=user["id"],
    )

    return {"checkout_url": checkout_url}


@router.post("/cancel")
async def cancel_subscription(user: dict = Depends(get_current_user)):
    """إلغاء الاشتراك"""
    sub = SubscriptionDB.get_active_for_user(user["id"])
    if not sub or not sub.get("ls_subscription_id"):
        raise HTTPException(404, "No active subscription")

    await LemonSqueezyClient.cancel_subscription(sub["ls_subscription_id"])
    audit(user["id"], "subscription_cancelled", "subscription", sub["id"])

    return {"success": True, "message": "تم إلغاء اشتراكك. سيستمر حتى نهاية الفترة المدفوعة."}


@router.post("/pause")
async def pause_subscription(user: dict = Depends(get_current_user)):
    """تجميد مؤقت بدلاً من الإلغاء"""
    sub = SubscriptionDB.get_active_for_user(user["id"])
    if not sub:
        raise HTTPException(404, "No active subscription")

    await LemonSqueezyClient.pause_subscription(sub["ls_subscription_id"])
    return {"success": True, "message": "تم تجميد اشتراكك. يمكنك استئنافه في أي وقت."}


@router.post("/webhook")
async def lemonsqueezy_webhook(
    request: Request,
    x_signature: str = Header(None)
):
    """استلام webhooks من Lemon Squeezy"""
    body = await request.body()

    if not verify_webhook_signature(body, x_signature or ""):
        logger.error("Invalid webhook signature")
        raise HTTPException(401, "Invalid signature")

    payload = await request.json()
    event_name = payload.get("meta", {}).get("event_name", "")
    data = payload.get("data", {})

    handlers = {
        "subscription_created":     handle_subscription_created,
        "subscription_updated":     handle_subscription_updated,
        "subscription_resumed":     handle_subscription_updated,
        "subscription_cancelled":   handle_subscription_updated,
        "subscription_payment_success": handle_payment_success,
        "subscription_payment_failed":  handle_payment_failed,
    }

    handler = handlers.get(event_name)
    if handler:
        try:
            await handler(data)
        except Exception as e:
            logger.error(f"Webhook handler error: {e}")
    else:
        logger.info(f"Unhandled event: {event_name}")

    return {"received": True}
