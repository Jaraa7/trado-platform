# Converter Agent - TRADO
from datetime import datetime

class ConverterAgent:
    def should_trigger(self, user_data):
        try:
            days = (datetime.utcnow() - datetime.fromisoformat(
                user_data.get("created_at", datetime.utcnow().isoformat()))).days
        except Exception:
            days = 0
        return days >= 3 or user_data.get("pricing_page_visits", 0) >= 1

    def generate_upsell(self, missed_pnl=0):
        return (f"TRADO Upgrade Offer\n"
                f"Missed ~${missed_pnl:.0f} this week on free plan.\n"
                f"Upgrade to Starter ($25/mo) for 5 bots.\n"
                "trado.app/pricing")
