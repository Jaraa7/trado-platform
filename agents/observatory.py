"""Observatory - TRADO system health"""
from supabase import create_client
from datetime import datetime, date

class Observatory:
    def __init__(self, config):
        self.supabase = create_client(config["SUPABASE_URL"], config["SUPABASE_SERVICE_KEY"])
        self.config = config
        self.monthly_costs = 135.0

    def check_health(self):
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "anthropic_key": bool(self.config.get("ANTHROPIC_API_KEY")),
            "telegram": bool(self.config.get("TELEGRAM_BOT_TOKEN"))
        }

    def daily_report(self, pnl, pnl_pct, trade_count):
        emoji = "[UP]" if pnl >= 0 else "[DOWN]"
        return (f"{emoji} TRADO Daily Report\n"
                f"PnL: ${pnl:+,.2f} ({pnl_pct:+.2f}%)\n"
                f"Trades: {trade_count}\n"
                f"Date: {date.today()}")

    def hard_stop_alert(self, loss_pct, balance):
        return f"HARD STOP ACTIVE | Loss: {loss_pct:.1f}% | Balance: ${balance:,.2f}"
