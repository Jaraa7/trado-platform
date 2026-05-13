"""Backtester Agent - TRADO | Weekly performance review"""
from supabase import create_client
from datetime import datetime, timedelta

class Backtester:
    def __init__(self, config):
        self.supabase = create_client(config["SUPABASE_URL"], config["SUPABASE_SERVICE_KEY"])

    def weekly_review(self):
        """Fetch last 7 days trades and calculate metrics"""
        since = (datetime.utcnow() - timedelta(days=7)).isoformat()
        res = self.supabase.table("trades").select("*").gte("opened_at", since).execute()
        trades = res.data or []
        if not trades:
            return {"win_rate": 0, "total_pnl": 0, "trade_count": 0}
        closed = [t for t in trades if t.get("net_pnl") is not None]
        wins = [t for t in closed if (t.get("net_pnl") or 0) > 0]
        total_pnl = sum(t.get("net_pnl", 0) for t in closed)
        win_rate = len(wins) / len(closed) * 100 if closed else 0
        avg_win  = sum(t["net_pnl"] for t in wins) / len(wins) if wins else 0
        losses = [t for t in closed if (t.get("net_pnl") or 0) <= 0]
        avg_loss = sum(t["net_pnl"] for t in losses) / len(losses) if losses else 0
        return {
            "trade_count": len(trades),
            "closed_count": len(closed),
            "win_rate": round(win_rate, 1),
            "total_pnl": round(total_pnl, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": abs(avg_win / avg_loss) if avg_loss != 0 else 999,
            "best_strategy": self._best_strategy(closed)
        }

    def _best_strategy(self, trades):
        from collections import defaultdict
        strat_pnl = defaultdict(float)
        for t in trades:
            strat_pnl[t.get("strategy","unknown")] += t.get("net_pnl", 0)
        return max(strat_pnl, key=strat_pnl.get, default="unknown") if strat_pnl else "unknown"
