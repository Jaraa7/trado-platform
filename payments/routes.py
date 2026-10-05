"""
💳 Tap Payments Routes — FastAPI
"""
from fastapi import APIRouter, Request, HTTPException, Header, Depends
from auth.service import get_current_user
from pydantic import BaseModel
from typing import Optional
from payments.tap import (
    build_checkout_url, handle_webhook,
    cancel_subscription, get_subscription, verify_webhook
)

router = APIRouter(prefix="/payments", tags=["payments"])


class CheckoutRequest(BaseModel):
    tier:    str
    billing: str = "monthly"
    user_id: str
    email:   str
    name:    str


class CancelRequest(BaseModel):
    subscription_id: str


@router.post("/checkout")
async def create_checkout(req: CheckoutRequest):
    """إنشاء رابط دفع"""
    try:
        result = await build_checkout_url(
            tier_slug=req.tier,
            billing=req.billing,
            user_id=req.user_id,
            email=req.email,
            name=req.name,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook/tap")
async def tap_webhook(request: Request, x_tap_signature: Optional[str] = Header(None)):
    """Tap Payments webhook"""
    body  = await request.body()
    event = await request.json()

    # تحقق من صحة الـ webhook — إلزامي (رفض أي طلب بدون توقيع صحيح)
    if not x_tap_signature or not verify_webhook(body, x_tap_signature):
        raise HTTPException(status_code=401, detail="Invalid or missing signature")

    from db.client import get_supabase
    db = get_supabase(service_role=True)
    return await handle_webhook(event, db)


def _assert_owns_subscription(user: dict, subscription_id: str):
    """التأكد أن الاشتراك يخص المستخدم الحالي"""
    from db.client import get_supabase
    db = get_supabase(service_role=True)
    row = (
        db.table("subscriptions")
        .select("user_id")
        .eq("tap_subscription_id", subscription_id)
        .limit(1)
        .execute()
    )
    if not row.data or str(row.data[0].get("user_id")) != str(user.get("id")):
        raise HTTPException(status_code=403, detail="Subscription does not belong to this user")


@router.post("/cancel")
async def cancel_sub(req: CancelRequest, user: dict = Depends(get_current_user)):
    """إلغاء اشتراك — يتطلب تسجيل دخول وملكية الاشتراك"""
    _assert_owns_subscription(user, req.subscription_id)
    result = await cancel_subscription(req.subscription_id)
    return result


@router.get("/subscription/{subscription_id}")
async def get_sub(subscription_id: str, user: dict = Depends(get_current_user)):
    """جلب تفاصيل اشتراك — يتطلب تسجيل دخول وملكية الاشتراك"""
    _assert_owns_subscription(user, subscription_id)
    return await get_subscription(subscription_id)
