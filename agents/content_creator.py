"""Content Creator Agent - TRADO | Model: Claude Sonnet 4.6"""
import anthropic
from datetime import date

class ContentCreator:
    def __init__(self, config):
        self.claude = anthropic.Anthropic(api_key=config["ANTHROPIC_API_KEY"])

    def create_trade_post(self, symbol, side, price, pnl, pnl_pct, duration_h):
        """Generate Arabic social media post from trade result"""
        direction = "BUY" if side == "buy" else "SELL"
        result_word = "ربح" if pnl >= 0 else "خسارة"
        emoji = "" if pnl >= 0 else ""
        post = (
            f"{emoji} TRADO | {direction} {symbol}\n"
            f"---------------------------\n"
            f"{result_word}: ${abs(pnl):.2f} ({pnl_pct:+.2f}%)\n"
            f"السعر: ${price:,.4f}\n"
            f"المدة: {duration_h:.1f} ساعة\n"
            f"---------------------------\n"
            f"#TRADO #trading #crypto"
        )
        return post

    def create_daily_summary(self, trades, total_pnl, win_rate):
        emoji = "" if total_pnl >= 0 else ""
        return (
            f"{emoji} TRADO | التقرير اليومي\n"
            f"---------------------------\n"
            f"الصفقات: {len(trades)}\n"
            f"الربح الصافي: ${total_pnl:+.2f}\n"
            f"نسبة النجاح: {win_rate:.1f}%\n"
            f"التاريخ: {date.today()}\n"
            f"---------------------------\n"
            f"#TRADO #trading"
        )
