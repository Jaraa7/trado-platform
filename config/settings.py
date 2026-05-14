"""
TRADO Platform — Central Configuration
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # AI APIs
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    deepseek_api_key: str = Field(default="", alias="DEEPSEEK_API_KEY")

    # Database
    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_key: str = Field(default="", alias="SUPABASE_KEY")
    supabase_service_key: str = Field(default="", alias="SUPABASE_SERVICE_KEY")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")

    # Vector DB
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_api_key: str = Field(default="", alias="QDRANT_API_KEY")

    # Exchanges
    binance_api_key: str = Field(default="", alias="BINANCE_API_KEY")
    binance_secret: str = Field(default="", alias="BINANCE_SECRET")
    binance_testnet: bool = Field(default=True, alias="BINANCE_TESTNET")

    bybit_api_key: str = Field(default="", alias="BYBIT_API_KEY")
    bybit_secret: str = Field(default="", alias="BYBIT_SECRET")
    bybit_testnet: bool = Field(default=True, alias="BYBIT_TESTNET")

    # Notifications
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_admin_chat_id: str = Field(default="", alias="TELEGRAM_ADMIN_CHAT_ID")

    # App
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Risk Limits
    max_risk_per_trade: float = Field(default=0.02, alias="MAX_RISK_PER_TRADE")
    max_daily_loss: float = Field(default=0.06, alias="MAX_DAILY_LOSS")
    max_monthly_drawdown: float = Field(default=0.15, alias="MAX_MONTHLY_DRAWDOWN")
    max_leverage: int = Field(default=3, alias="MAX_LEVERAGE")


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
