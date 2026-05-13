import os

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

def validate_config(cfg):
    required = ["BINANCE_API_KEY","ANTHROPIC_API_KEY","SUPABASE_URL","SUPABASE_SERVICE_KEY"]
    return [k for k in required if not cfg.get(k)]