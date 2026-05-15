import os
from dataclasses import dataclass

@dataclass
class Settings:
    # Exchange APIs
    BINANCE_API_KEY: str = ""
    BINANCE_API_SECRET: str = ""
    BYBIT_API_KEY: str = ""
    BYBIT_API_SECRET: str = ""
    OKX_API_KEY: str = ""
    OKX_API_SECRET: str = ""
    # AI APIs
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""
    # Database
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    REDIS_URL: str = ""
    QDRANT_URL: str = ""
    QDRANT_API_KEY: str = ""
    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_ADMIN_CHAT_ID: str = ""
    # Payment
    PADDLE_API_KEY: str = ""
    MYFATOORAH_API_KEY: str = ""
    # App
    DOMAIN: str = "trado-bot.fly.dev"
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"

    def __post_init__(self):
        for field_name in self.__dataclass_fields__:
            env_val = os.getenv(field_name, "")
            if env_val:
                setattr(self, field_name, env_val)

settings = Settings()

def load_config():
    return {
        "BINANCE_API_KEY": os.getenv("BINANCE_API_KEY",""),
        "BINANCE_API_SECRET": os.getenv("BINANCE_API_SECRET",""),
        "BYBIT_API_KEY": os.getenv("BYBIT_API_KEY",""),
        "BYBIT_API_SECRET": os.getenv("BYBIT_API_SECRET",""),
        "OKX_API_KEY": os.getenv("OKX_API_KEY",""),
        "OKX_API_SECRET": os.getenv("OKX_API_SECRET",""),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY",""),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY",""),
        "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY",""),
        "SUPABASE_URL": os.getenv("SUPABASE_URL",""),
        "SUPABASE_SERVICE_KEY": os.getenv("SUPABASE_SERVICE_KEY",""),
        "REDIS_URL": os.getenv("REDIS_URL",""),
        "QDRANT_URL": os.getenv("QDRANT_URL",""),
        "QDRANT_API_KEY": os.getenv("QDRANT_API_KEY",""),
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN",""),
        "TELEGRAM_ADMIN_ID": os.getenv("TELEGRAM_ADMIN_CHAT_ID",""),
        "PADDLE_API_KEY": os.getenv("PADDLE_API_KEY",""),
        "MYFATOORAH_API_KEY": os.getenv("MYFATOORAH_API_KEY",""),
        "DOMAIN": os.getenv("DOMAIN","trado.app"),
    }
