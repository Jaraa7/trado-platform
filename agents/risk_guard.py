"""Risk Guard Agent - TRADO | Protects capital 24/7"""
from datetime import datetime, date
from supabase import create_client
from loguru import logger

class RiskGuard:
    MAX_DAILY_LOSS_PCT   = 7.0
    MAX_WEEKLY_LOSS_PCT  = 15.0
    MAX_SINGLE_TRADE_PCT = 2.0
    MAX_OPEN_TRADES      = 5

    def __init__(self, config, initial_balance):
        self.supabase = create_client(config["SUPABASE_URL"], config["SUPABASE_SERVICE_KEY"])
        self._daily_loss = 0.0
        self._weekly_loss = 0.0
        self._open_trades = 0
        self._hard_stop = False
        self._last_reset = date.today()

    def approve_trade(self, analysis, balance):
        if self._hard_stop: return {"approved":False,"reason":"HARD_STOP"}
        if self._open_trades >= self.MAX_OPEN_TRADES: return {"approved":False,"reason":"MAX_TRADES"}
        daily_pct = (self._daily_loss / balance) * 100
        if daily_pct >= self.MAX_DAILY_LOSS_PCT: return {"approved":False,"reason":"DAILY_LIMIT"}
        weekly_pct = (self._weekly_loss / balance) * 100
        if weekly_pct >= self.MAX_WEEKLY_LOSS_PCT:
            self._hard_stop = True
            logger.critical("[RiskGuard] HARD STOP TRIGGERED!")
            return {"approved":False,"reason":"WEEKLY_HARD_STOP"}
        stop = analysis.get("stop_loss")
        if not stop: return {"approved":False,"reason":"NO_STOP_LOSS"}
        entry = analysis.get("entry_price", 0)
        size_pct = analysis.get("position_size_pct", 2.0)
        pos_val = balance * (size_pct / 100)
        risk_pct = abs(entry - stop) / entry * 100 if entry else 99
        if risk_pct > self.MAX_SINGLE_TRADE_PCT:
            return {"approved":False,"reason":f"RISK_TOO_HIGH_{risk_pct:.1f}pct"}
        self._open_trades += 1
        return {"approved":True,"position_value":pos_val,"risk_pct":risk_pct}

    def record_result(self, pnl):
        if pnl < 0:
            self._daily_loss += abs(pnl)
            self._weekly_loss += abs(pnl)
        self._open_trades = max(0, self._open_trades - 1)

    @property
    def is_hard_stop(self): return self._hard_stop

    def manual_resume(self):
        self._hard_stop = False
        self._daily_loss = 0.0
        self._weekly_loss = 0.0
        logger.warning("[RiskGuard] Manually resumed")