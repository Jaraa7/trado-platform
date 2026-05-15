import pytest
import asyncio
from unittest.mock import MagicMock, patch

def test_rsi_calculation():
    from agents.scanner import ScannerAgent
    scanner = ScannerAgent.__new__(ScannerAgent)
    closes = [100,102,101,103,105,104,106,108,107,109,110,112,111,113,115]
    rsi = scanner._calc_rsi(closes)
    assert 0 <= rsi <= 100, f"RSI out of range: {rsi}"
    assert isinstance(rsi, float)

def test_layer_one_filter():
    from agents.scanner import ScannerAgent
    scanner = ScannerAgent.__new__(ScannerAgent)
    scanner.blacklist = set()
    scanner.PRICE_CHANGE_THRESHOLD = 2.0
    tickers = [
        {"symbol":"BTC/USDT","change":5.0,"volume":2000000},
        {"symbol":"ETH/USDT","change":0.5,"volume":1500000},
        {"symbol":"BNB/USDT","change":3.0,"volume":1200000},
    ]
    result = scanner.layer_one_filter(tickers)
    assert len(result) == 2
    symbols = [r["symbol"] for r in result]
    assert "BTC/USDT" in symbols
    assert "BNB/USDT" in symbols

def test_risk_guard_approval():
    from agents.risk_guard import RiskGuard
    guard = RiskGuard.__new__(RiskGuard)
    guard._hard_stop   = False
    guard._open_trades = 0
    guard._daily_loss  = 0.0
    guard._weekly_loss = 0.0
    guard.MAX_OPEN_TRADES      = 5
    guard.MAX_DAILY_LOSS_PCT   = 7.0
    guard.MAX_WEEKLY_LOSS_PCT  = 15.0
    guard.MAX_SINGLE_TRADE_PCT = 2.0
    from datetime import date
    guard._last_reset = date.today()
    analysis = {"entry_price":100,"stop_loss":98,"position_size_pct":2}
    result = guard.approve_trade(analysis, 1000)
    assert result["approved"] == True
    assert result["risk_pct"] == 2.0

def test_risk_guard_hard_stop():
    from agents.risk_guard import RiskGuard
    guard = RiskGuard.__new__(RiskGuard)
    guard._hard_stop = True
    guard._open_trades = 0
    guard._daily_loss = 0.0
    guard._weekly_loss = 0.0
    from datetime import date
    guard._last_reset = date.today()
    result = guard.approve_trade({}, 1000)
    assert result["approved"] == False
    assert result["reason"] == "HARD_STOP"