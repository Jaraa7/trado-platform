"""
🔐 TradoAI Authentication System
JWT + Supabase Auth + Magic Links
"""
import os
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from loguru import logger

from db.client import UserDB, audit, get_supabase


# ════════════════════════════════════════════════════════════════════
# Configuration
# ════════════════════════════════════════════════════════════════════

JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7    # 7 days
REFRESH_EXPIRATION_DAYS = 30

security = HTTPBearer()


# ════════════════════════════════════════════════════════════════════
# Models
# ════════════════════════════════════════════════════════════════════

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str = None
    country_code: str = None
    referral_code: str = None


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class MagicLinkRequest(BaseModel):
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


# ════════════════════════════════════════════════════════════════════
# Token utilities
# ════════════════════════════════════════════════════════════════════

def create_access_token(user_id: str, email: str, extra: dict = None) -> str:
    """إنشاء JWT access token"""
    payload = {
        "sub": user_id,
        "email": email,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "type": "access",
        **(extra or {})
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """إنشاء refresh token (مدة أطول)"""
    payload = {
        "sub": user_id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(days=REFRESH_EXPIRATION_DAYS),
        "type": "refresh"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    """فحص صحة الـ token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")


# ════════════════════════════════════════════════════════════════════
# Dependencies
# ════════════════════════════════════════════════════════════════════

async def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """fastapi dependency للحصول على المستخدم الحالي"""
    payload = verify_token(creds.credentials)
    if payload.get("type") != "access":
        raise HTTPException(401, "Invalid token type")

    user = UserDB.get_by_id(payload["sub"])
    if not user:
        raise HTTPException(404, "User not found")
    if user.get("status") != "active":
        raise HTTPException(403, "Account is not active")

    return user


async def get_optional_user(request: Request) -> dict | None:
    """مستخدم اختياري — None إذا لم يكن مسجلاً"""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    try:
        token = auth.split(" ", 1)[1]
        payload = verify_token(token)
        return UserDB.get_by_id(payload["sub"])
    except:
        return None


# ════════════════════════════════════════════════════════════════════
# Auth Operations
# ════════════════════════════════════════════════════════════════════

class AuthService:

    @staticmethod
    async def sign_up(req: SignUpRequest, ip: str = None) -> TokenResponse:
        """تسجيل مستخدم جديد"""
        # تحقق من عدم وجود نفس الإيميل
        existing = UserDB.get_by_email(req.email)
        if existing:
            raise HTTPException(409, "Email already registered")

        # إنشاء حساب في Supabase Auth
        sb = get_supabase(service_role=True)
        try:
            auth_result = sb.auth.sign_up({
                "email": req.email,
                "password": req.password,
            })
            auth_id = auth_result.user.id if auth_result.user else None
        except Exception as e:
            logger.error(f"Supabase signup error: {e}")
            raise HTTPException(400, f"Sign-up failed: {str(e)[:100]}")

        # حفظ في users table
        user = UserDB.create(
            email=req.email,
            full_name=req.full_name,
            country_code=req.country_code,
            auth_id=auth_id,
        )

        if not user:
            raise HTTPException(500, "Failed to create user")

        # ربط الـ referral
        if req.referral_code:
            try:
                sb.table("users").update({
                    "referred_by": req.referral_code
                }).eq("id", user["id"]).execute()
            except:
                pass    # لا تفشل التسجيل لأجل referral

        # إنشاء default settings
        sb.table("user_settings").insert({
            "user_id": user["id"]
        }).execute()

        # إنشاء trial subscription
        from agents.financial.agents import TIERS    # سننقلها
        sb.table("subscriptions").insert({
            "user_id": user["id"],
            "tier": "trial",
            "amount": 0,
            "current_period_end": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }).execute()

        # Audit
        audit(user["id"], "user_signup", "user", user["id"],
              metadata={"method": "email"}, ip=ip)

        # Tokens
        access = create_access_token(user["id"], user["email"])
        refresh = create_refresh_token(user["id"])

        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            expires_in=JWT_EXPIRATION_HOURS * 3600,
            user={
                "id": user["id"],
                "email": user["email"],
                "full_name": user.get("full_name"),
                "country_code": user.get("country_code"),
                "tier": "trial",
            }
        )

    @staticmethod
    async def sign_in(req: SignInRequest, ip: str = None) -> TokenResponse:
        """تسجيل دخول"""
        # عبر Supabase Auth
        sb = get_supabase(service_role=False)
        try:
            auth_result = sb.auth.sign_in_with_password({
                "email": req.email,
                "password": req.password,
            })
        except Exception as e:
            audit(None, "login_failed", metadata={"email": req.email, "reason": str(e)[:100]}, ip=ip)
            raise HTTPException(401, "Invalid credentials")

        user = UserDB.get_by_email(req.email)
        if not user:
            raise HTTPException(404, "User not found")

        # Update last active
        UserDB.update(user["id"], last_active_at=datetime.utcnow().isoformat())

        audit(user["id"], "login_success", "user", user["id"], ip=ip)

        access = create_access_token(user["id"], user["email"])
        refresh = create_refresh_token(user["id"])

        # Get current tier
        from db.client import SubscriptionDB
        sub = SubscriptionDB.get_active_for_user(user["id"])
        tier = sub.get("tier") if sub else "free"

        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            expires_in=JWT_EXPIRATION_HOURS * 3600,
            user={
                "id": user["id"],
                "email": user["email"],
                "full_name": user.get("full_name"),
                "tier": tier,
            }
        )

    @staticmethod
    async def magic_link(email: str) -> dict:
        """إرسال magic link للدخول بدون كلمة مرور"""
        sb = get_supabase(service_role=True)
        try:
            sb.auth.sign_in_with_otp({"email": email})
            return {"success": True, "message": "تم إرسال رابط الدخول إلى بريدك"}
        except Exception as e:
            logger.error(f"Magic link error: {e}")
            return {"success": True, "message": "إذا كان البريد مسجلاً، ستصلك رسالة"}

    @staticmethod
    async def refresh_token(refresh_token: str) -> dict:
        """تجديد الـ access token"""
        payload = verify_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(401, "Invalid refresh token")

        user = UserDB.get_by_id(payload["sub"])
        if not user:
            raise HTTPException(404, "User not found")

        new_access = create_access_token(user["id"], user["email"])
        return {
            "access_token": new_access,
            "token_type": "bearer",
            "expires_in": JWT_EXPIRATION_HOURS * 3600
        }

    @staticmethod
    async def sign_out(user_id: str, ip: str = None):
        """تسجيل خروج"""
        audit(user_id, "logout", "user", user_id, ip=ip)
        return {"success": True}


# ════════════════════════════════════════════════════════════════════
# Tier Limits Enforcement
# ════════════════════════════════════════════════════════════════════

def check_tier_limit(user: dict, feature: str) -> bool:
    """فحص حدود الباقة"""
    from db.client import SubscriptionDB

    sub = SubscriptionDB.get_active_for_user(user["id"])
    if not sub:
        raise HTTPException(403, "Active subscription required")

    tier = sub["tier"]

    # حدود الإشارات
    SIGNALS_PER_DAY = {
        "trial": 10, "micro": 5, "starter": 15, "pro": 50,
        "elite": 9999, "whale": 9999, "institutional": 9999,
        "founder": 9999, "enterprise": 9999
    }

    if feature == "signals":
        # احسب اليوم
        sb = get_supabase()
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0).isoformat()
        result = sb.table("agent_usage").select("id", count="exact") \
            .eq("user_id", user["id"]) \
            .gte("created_at", today_start) \
            .execute()
        used = result.count or 0
        limit = SIGNALS_PER_DAY.get(tier, 0)

        if used >= limit:
            raise HTTPException(429, f"تجاوزت حد الإشارات اليومية ({limit}). ترقّى لباقة أعلى.")

    return True


def require_tier(*allowed_tiers: str):
    """Decorator لتحديد الـ tiers المسموحة"""
    async def dep(user: dict = Depends(get_current_user)):
        from db.client import SubscriptionDB
        sub = SubscriptionDB.get_active_for_user(user["id"])
        if not sub or sub["tier"] not in allowed_tiers:
            raise HTTPException(403, f"This feature requires one of: {', '.join(allowed_tiers)}")
        return user
    return dep
