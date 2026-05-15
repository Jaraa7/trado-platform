"""
🔐 Auth API Routes
"""
from fastapi import APIRouter, Request, Depends, HTTPException
from auth.service import (
    AuthService, SignUpRequest, SignInRequest, MagicLinkRequest,
    get_current_user, TokenResponse
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=TokenResponse)
async def signup(request: Request, body: SignUpRequest):
    """تسجيل مستخدم جديد"""
    ip = request.client.host if request.client else None
    return await AuthService.sign_up(body, ip=ip)


@router.post("/signin", response_model=TokenResponse)
async def signin(request: Request, body: SignInRequest):
    """تسجيل دخول"""
    ip = request.client.host if request.client else None
    return await AuthService.sign_in(body, ip=ip)


@router.post("/magic-link")
async def magic_link(body: MagicLinkRequest):
    """إرسال magic link"""
    return await AuthService.magic_link(body.email)


@router.post("/refresh")
async def refresh_token(body: dict):
    """تجديد access token"""
    refresh = body.get("refresh_token")
    if not refresh:
        raise HTTPException(400, "refresh_token required")
    return await AuthService.refresh_token(refresh)


@router.post("/signout")
async def signout(request: Request, user: dict = Depends(get_current_user)):
    """تسجيل خروج"""
    ip = request.client.host if request.client else None
    return await AuthService.sign_out(user["id"], ip=ip)


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    """معلومات المستخدم الحالي"""
    from db.client import SubscriptionDB, get_supabase

    sub = SubscriptionDB.get_active_for_user(user["id"])

    # User stats
    sb = get_supabase()
    stats = sb.table("trades").select("id, pnl_usd", count="exact") \
        .eq("user_id", user["id"]).execute()

    total_trades = stats.count or 0
    total_pnl = sum(float(t.get("pnl_usd") or 0) for t in stats.data)

    return {
        "user": user,
        "subscription": sub,
        "stats": {
            "total_trades": total_trades,
            "total_pnl": round(total_pnl, 2),
        }
    }
