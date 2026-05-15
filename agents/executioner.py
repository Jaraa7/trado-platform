"""Executioner Agent - TRADO | Trade execution via CCXT"""
import ccxt.async_support as ccxt
from supabase import create_client
from loguru import logger
from datetime import datetime

class Executioner:
    def __init__(self, config):
        self.config = config
        self.supabase = create_client(config["SUPABASE_URL"], config["SUPABASE_SERVICE_KEY"])
        self.exchanges = {
            "binance": ccxt.binance({"apiKey":config["BINANCE_API_KEY"],"secret":config["BINANCE_API_SECRET"],"enableRateLimit":True}),
            "bybit":   ccxt.bybit({"apiKey":config["BYBIT_API_KEY"],"secret":config["BYBIT_API_SECRET"],"enableRateLimit":True}),
            "okx":     ccxt.okx({"apiKey":config["OKX_API_KEY"],"secret":config["OKX_API_SECRET"],"enableRateLimit":True}),
        }

    async def execute(self, analysis, approval):
        symbol   = analysis["symbol"]
        exchange_name = analysis["exchange"]
        decision = analysis["decision"]
        entry    = analysis["entry_price"]
        sl       = analysis["stop_loss"]
        tp1      = analysis["take_profit_1"]
        tp2      = analysis.get("take_profit_2", tp1 * 1.02)
        pos_val  = approval["position_value"]
        exchange = self.exchanges[exchange_name]
        side     = "buy" if decision == "BUY" else "sell"

        try:
            ticker = await exchange.fetch_ticker(symbol)
            current_price = ticker["last"]
            amount = pos_val / current_price
            order = await exchange.create_order(symbol, "market", side, amount)
            actual_price = order.get("average", current_price)
            trade_record = {
                "symbol": symbol, "exchange": exchange_name,
                "side": side, "entry_price": actual_price,
                "stop_loss": sl, "take_profit_1": tp1, "take_profit_2": tp2,
                "position_value": pos_val, "order_id": order["id"],
                "status": "open", "strategy": analysis.get("strategy","momentum"),
                "confidence": analysis.get("confidence",0),
                "reason": analysis.get("reason_arabic",""),
                "opened_at": datetime.utcnow().isoformat()
            }
            self.supabase.table("trades").insert(trade_record).execute()
            logger.info(f"[Executioner] {side.upper()} {symbol} @ {actual_price}")
            return {"success": True, "trade": trade_record, "order": order}
        except Exception as e:
            logger.error(f"[Executioner] FAILED {symbol}: {e}")
            return {"success": False, "error": str(e), "symbol": symbol}

    async def close_all(self):
        for ex in self.exchanges.values():
            await ex.close()