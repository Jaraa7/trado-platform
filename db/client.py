"""
TRADO Database Layer
Supabase PostgreSQL client with encrypted secrets
"""
import os
from typing import Optional
from datetime import datetime
from loguru import logger
from supabase import create_client, Client
from cryptography.fernet import Fernet
import base64, hashlib


# ════════════════════════════════════════════════════════════════════
# Supabase Client (Singleton)
# ════════════════════════════════════════════════════════════════════

_client: Optional[Client] = None


def get_supabase(service_role: bool = False) -> Client:
    """احصل على Supabase client (singleton)"""
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv(
            "SUPABASE_SERVICE_KEY" if service_role else "SUPABASE_ANON_KEY",
            ""
        )
        if not url or not key:
            raise RuntimeError("Supabase credentials missing")
        _client = create_client(url, key)
        logger.info(f"✅ Supabase connected ({'service' if service_role else 'anon'})")
    return _client


# ════════════════════════════════════════════════════════════════════
# Encryption (for API keys storage)
# ════════════════════════════════════════════════════════════════════

def _get_master_key() -> bytes:
    """يحصل على مفتاح التشفير الرئيسي من env"""
    secret = os.getenv("ENCRYPTION_SECRET", "default-dev-secret-change-me")
    key_material = hashlib.sha256(secret.encode()).digest()
    return base64.urlsafe_b64encode(key_material)


def encrypt_secret(plain: str) -> str:
    """تشفير قيمة حساسة (مثل API keys)"""
    f = Fernet(_get_master_key())
    return f.encrypt(plain.encode()).decode()


def decrypt_secret(encrypted: str) -> str:
    """فك تشفير قيمة"""
    f = Fernet(_get_master_key())
    return f.decrypt(encrypted.encode()).decode()


# ════════════════════════════════════════════════════════════════════
# User Operations
# ════════════════════════════════════════════════════════════════════

class UserDB:
    @staticmethod
    def create(email: str, full_name: str = None, country_code: str = None, **kwargs) -> dict:
        """إنشاء مستخدم جديد"""
        sb = get_supabase(service_role=True)
        data = {
            "email": email,
            "full_name": full_name,
            "country_code": country_code,
            "referral_code": _generate_referral_code(email),
            **kwargs
        }
        result = sb.table("users").insert(data).execute()
        logger.info(f"User created: {email}")
        return result.data[0] if result.data else None

    @staticmethod
    def get_by_email(email: str) -> Optional[dict]:
        sb = get_supabase()
        result = sb.table("users").select("*").eq("email", email).execute()
        return result.data[0] if result.data else None

    @staticmethod
    def get_by_id(user_id: str) -> Optional[dict]:
        sb = get_supabase()
        result = sb.table("users").select("*").eq("id", user_id).execute()
        return result.data[0] if result.data else None

    @staticmethod
    def get_by_telegram(chat_id: int) -> Optional[dict]:
        sb = get_supabase()
        result = sb.table("users").select("*").eq("telegram_chat_id", chat_id).execute()
        return result.data[0] if result.data else None

    @staticmethod
    def update(user_id: str, **fields) -> dict:
        sb = get_supabase()
        result = sb.table("users").update(fields).eq("id", user_id).execute()
        return result.data[0] if result.data else None


# ════════════════════════════════════════════════════════════════════
# Exchange Account Operations
# ════════════════════════════════════════════════════════════════════

class ExchangeDB:
    @staticmethod
    def add(user_id: str, exchange: str, api_key: str, api_secret: str,
            passphrase: str = None, is_testnet: bool = False, label: str = "Main") -> dict:
        """إضافة حساب منصة جديد مع تشفير المفاتيح"""
        sb = get_supabase()
        data = {
            "user_id": user_id,
            "exchange": exchange,
            "account_label": label,
            "is_testnet": is_testnet,
            "api_key_encrypted": encrypt_secret(api_key),
            "api_secret_encrypted": encrypt_secret(api_secret),
            "passphrase_encrypted": encrypt_secret(passphrase) if passphrase else None,
        }
        result = sb.table("exchange_accounts").insert(data).execute()
        logger.info(f"Exchange added: {exchange} for user {user_id[:8]}")
        return result.data[0] if result.data else None

    @staticmethod
    def get_for_user(user_id: str, exchange: str = None) -> list[dict]:
        """جلب حسابات المستخدم (مع فك التشفير)"""
        sb = get_supabase()
        q = sb.table("exchange_accounts").select("*").eq("user_id", user_id).eq("status", "active")
        if exchange:
            q = q.eq("exchange", exchange)
        result = q.execute()

        # فك التشفير
        for account in result.data:
            try:
                account["api_key"] = decrypt_secret(account["api_key_encrypted"])
                account["api_secret"] = decrypt_secret(account["api_secret_encrypted"])
                if account.get("passphrase_encrypted"):
                    account["passphrase"] = decrypt_secret(account["passphrase_encrypted"])
            except Exception as e:
                logger.error(f"Decryption failed for account {account['id']}: {e}")
        return result.data


# ════════════════════════════════════════════════════════════════════
# Signal Operations
# ════════════════════════════════════════════════════════════════════

class SignalDB:
    @staticmethod
    def create(symbol: str, direction: str, entry: float, sl: float, tp: float,
               confidence: int = 50, ai_analysis: str = "", agent_id: str = "unknown",
               **kwargs) -> dict:
        sb = get_supabase(service_role=True)
        data = {
            "symbol": symbol,
            "direction": direction,
            "entry_price": entry,
            "stop_loss": sl,
            "take_profit_1": tp,
            "confidence": confidence,
            "ai_analysis": ai_analysis[:5000],    # truncate
            "generated_by": agent_id,
            "risk_reward": round(abs(tp - entry) / abs(entry - sl), 2) if entry != sl else 0,
            **kwargs
        }
        result = sb.table("signals").insert(data).execute()
        return result.data[0] if result.data else None

    @staticmethod
    def recent(limit: int = 20) -> list[dict]:
        sb = get_supabase()
        result = (
            sb.table("signals")
            .select("*")
            .eq("status", "active")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data


# ════════════════════════════════════════════════════════════════════
# Trade Operations
# ════════════════════════════════════════════════════════════════════

class TradeDB:
    @staticmethod
    def create(user_id: str, symbol: str, direction: str, entry_price: float,
               quantity: float, leverage: int = 1, signal_id: str = None,
               exchange_order_id: str = None, **kwargs) -> dict:
        sb = get_supabase(service_role=True)
        data = {
            "user_id": user_id,
            "signal_id": signal_id,
            "symbol": symbol,
            "direction": direction,
            "entry_price": entry_price,
            "quantity": quantity,
            "notional_value": quantity * entry_price,
            "leverage": leverage,
            "exchange_order_id": exchange_order_id,
            "status": "open",
            **kwargs
        }
        result = sb.table("trades").insert(data).execute()
        return result.data[0] if result.data else None

    @staticmethod
    def close(trade_id: str, exit_price: float, pnl_usd: float, fees: float = 0) -> dict:
        sb = get_supabase(service_role=True)
        result = (
            sb.table("trades")
            .update({
                "exit_price": exit_price,
                "pnl_usd": pnl_usd,
                "fees_usd": fees,
                "status": "closed",
                "closed_at": datetime.utcnow().isoformat()
            })
            .eq("id", trade_id)
            .execute()
        )
        return result.data[0] if result.data else None

    @staticmethod
    def open_for_user(user_id: str) -> list[dict]:
        sb = get_supabase()
        result = (
            sb.table("trades")
            .select("*")
            .eq("user_id", user_id)
            .eq("status", "open")
            .execute()
        )
        return result.data


# ════════════════════════════════════════════════════════════════════
# Subscription Operations
# ════════════════════════════════════════════════════════════════════

class SubscriptionDB:
    @staticmethod
    def create(user_id: str, tier: str, amount: float, billing_cycle: str = "monthly", **kwargs) -> dict:
        sb = get_supabase(service_role=True)
        data = {
            "user_id": user_id,
            "tier": tier,
            "amount": amount,
            "billing_cycle": billing_cycle,
            "status": "active",
            **kwargs
        }
        result = sb.table("subscriptions").insert(data).execute()
        return result.data[0] if result.data else None

    @staticmethod
    def get_active_for_user(user_id: str) -> Optional[dict]:
        sb = get_supabase()
        result = (
            sb.table("subscriptions")
            .select("*")
            .eq("user_id", user_id)
            .eq("status", "active")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None


# ════════════════════════════════════════════════════════════════════
# Waitlist
# ════════════════════════════════════════════════════════════════════

class WaitlistDB:
    @staticmethod
    def add(email: str, **kwargs) -> dict:
        sb = get_supabase(service_role=True)
        try:
            result = sb.table("waitlist").insert({"email": email, **kwargs}).execute()
            logger.info(f"Waitlist: {email}")
            return result.data[0] if result.data else None
        except Exception as e:
            if "duplicate" in str(e).lower():
                logger.info(f"Email already on waitlist: {email}")
                return None
            raise

    @staticmethod
    def count() -> int:
        sb = get_supabase()
        result = sb.table("waitlist").select("id", count="exact").execute()
        return result.count or 0


# ════════════════════════════════════════════════════════════════════
# Audit Log
# ════════════════════════════════════════════════════════════════════

def audit(user_id: str, action: str, resource_type: str = None,
          resource_id: str = None, metadata: dict = None,
          ip: str = None, pii: bool = False):
    """تسجيل عملية في audit log"""
    try:
        sb = get_supabase(service_role=True)
        sb.table("audit_logs").insert({
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "metadata": metadata or {},
            "ip_address": ip,
            "pii_accessed": pii
        }).execute()
    except Exception as e:
        logger.error(f"Audit log failed: {e}")


# ════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════

def _generate_referral_code(seed: str) -> str:
    """توليد referral code من email"""
    import hashlib
    h = hashlib.sha256(seed.encode()).hexdigest()[:8].upper()
    return f"TRD{h}"
