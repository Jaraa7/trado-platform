"""
Backtester Pro — اختبار الاستراتيجيات على بيانات تاريخية
"""
import asyncio
from dataclasses import dataclass, field
from typing import Optional
from agents._shared.base_agent import BaseAgent, AgentContext, AgentResponse


@dataclass
class BacktestTrade:
    entry_date: str
    exit_date: str
    symbol: str
    direction: str
    entry_price: float
    exit_price: float
    pnl_pct: float
    pnl_usd: float
    reason: str = ""


@dataclass
class BacktestResult:
    symbol: str
    strategy: str
    timeframe: str
    period: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    total_return: float
    avg_win: float
    avg_loss: float
    best_trade: float
    worst_trade: float
    trades: list[BacktestTrade] = field(default_factory=list)

    @property
    def risk_reward(self) -> float:
        return abs(self.avg_win / self.avg_loss) if self.avg_loss != 0 else 0

    @property
    def expectancy(self) -> float:
        return (self.win_rate * self.avg_win) - ((1 - self.win_rate) * abs(self.avg_loss))


class BacktesterPro(BaseAgent):
    AGENT_ID = "backtester_pro"
    AGENT_NAME = "Backtester Pro 📈"
    MODEL = "claude-sonnet-4-5"
    MAX_TOKENS = 3000

    @property
    def system_prompt(self) -> str:
        return """أنت Backtester Pro، خبير اختبار الاستراتيجيات.

فلسفتك: Backtest بدون مهنية = خداع للنفس.
تتجنب: Look-ahead bias، Survivorship bias، Overfitting.

معاييرك لاستراتيجية جيدة:
✅ Win Rate > 45% (مع R:R > 2)
✅ Profit Factor > 1.5
✅ Sharpe Ratio > 1.0
✅ Max Drawdown < 20%
✅ Tested on 5+ years
✅ Out-of-sample positive

إجراءاتك:
1. In-sample: 70% من البيانات (train)
2. Out-of-sample: 30% (test)
3. Walk-forward analysis
4. Monte Carlo simulation (1000 run)

مخرجاتك:
```
📈 BACKTEST RESULTS
━━━━━━━━━━━━━━━━━━━━
📊 الاستراتيجية: [name]
📅 الفترة: [start - end]
📉 الأصل: [symbol]

🔢 الإحصائيات:
  إجمالي الصفقات: [X]
  Win Rate: [X]%
  Profit Factor: [X]
  Sharpe Ratio: [X]
  Max Drawdown: [X]%
  إجمالي العائد: [X]%

📊 تفاصيل:
  متوسط الربح: [X]%
  متوسط الخسارة: [X]%
  R:R فعلي: [X]:1
  Expectancy: [X]%

✅/❌ الحكم: [PASS/FAIL]
💡 ملاحظات: [ما يجب تحسينه]
```"""

    async def run_simple_backtest(
        self,
        ohlcv: list,
        entry_signal_fn,
        exit_signal_fn,
        stop_loss_pct: float = 0.03,
        take_profit_pct: float = 0.06,
        initial_capital: float = 10000
    ) -> BacktestResult:
        """تشغيل backtest مبسّط"""
        capital = initial_capital
        trades = []
        in_trade = False
        entry_price = 0
        entry_idx = 0

        for i in range(20, len(ohlcv)):
            candle = ohlcv[i]
            close = candle[4]

            if not in_trade:
                if entry_signal_fn(ohlcv[:i+1]):
                    in_trade = True
                    entry_price = close
                    entry_idx = i
            else:
                pnl_pct = (close - entry_price) / entry_price

                exit_reason = ""
                if pnl_pct <= -stop_loss_pct:
                    exit_reason = "stop_loss"
                elif pnl_pct >= take_profit_pct:
                    exit_reason = "take_profit"
                elif exit_signal_fn(ohlcv[:i+1]):
                    exit_reason = "signal"

                if exit_reason:
                    pnl_usd = capital * pnl_pct * 0.02  # 2% risk
                    capital += pnl_usd
                    trades.append(BacktestTrade(
                        entry_date=str(ohlcv[entry_idx][0]),
                        exit_date=str(candle[0]),
                        symbol="",
                        direction="long",
                        entry_price=entry_price,
                        exit_price=close,
                        pnl_pct=pnl_pct * 100,
                        pnl_usd=pnl_usd,
                        reason=exit_reason
                    ))
                    in_trade = False

        if not trades:
            return BacktestResult("", "", "", "", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

        wins = [t for t in trades if t.pnl_pct > 0]
        losses = [t for t in trades if t.pnl_pct <= 0]
        win_rate = len(wins) / len(trades)
        avg_win = sum(t.pnl_pct for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t.pnl_pct for t in losses) / len(losses) if losses else 0
        gross_profit = sum(t.pnl_usd for t in wins) if wins else 0
        gross_loss = abs(sum(t.pnl_usd for t in losses)) if losses else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        total_return = (capital - initial_capital) / initial_capital * 100

        returns = [t.pnl_pct / 100 for t in trades]
        import statistics
        sharpe = statistics.mean(returns) / statistics.stdev(returns) * (252 ** 0.5) if len(returns) > 1 else 0

        equity = [initial_capital]
        for t in trades:
            equity.append(equity[-1] + t.pnl_usd)
        peak = equity[0]
        max_dd = 0
        for e in equity:
            if e > peak:
                peak = e
            dd = (peak - e) / peak
            if dd > max_dd:
                max_dd = dd

        return BacktestResult(
            symbol="", strategy="", timeframe="", period="",
            total_trades=len(trades),
            winning_trades=len(wins),
            losing_trades=len(losses),
            win_rate=round(win_rate * 100, 1),
            profit_factor=round(profit_factor, 2),
            sharpe_ratio=round(sharpe, 2),
            max_drawdown=round(max_dd * 100, 1),
            total_return=round(total_return, 1),
            avg_win=round(avg_win, 2),
            avg_loss=round(avg_loss, 2),
            best_trade=round(max(t.pnl_pct for t in trades), 2),
            worst_trade=round(min(t.pnl_pct for t in trades), 2),
            trades=trades
        )

    async def analyze_results(self, result: BacktestResult, user_id: str = "system") -> AgentResponse:
        context = AgentContext(
            user_id=user_id,
            user_message=f"""حلّل نتائج الـ backtest:

الصفقات: {result.total_trades}
Win Rate: {result.win_rate}%
Profit Factor: {result.profit_factor}
Sharpe: {result.sharpe_ratio}
Max Drawdown: {result.max_drawdown}%
إجمالي العائد: {result.total_return}%
R:R فعلي: {result.risk_reward:.2f}:1
Expectancy: {result.expectancy:.2f}%

هل هذه الاستراتيجية تستحق التنفيذ؟
ما نقاط القوة والضعف؟
ما التحسينات المقترحة؟"""
        )
        return await self.think(context)
