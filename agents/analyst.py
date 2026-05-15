"""
Analyst Agent - TRADO
Model: Claude Sonnet 4.6
"""
import anthropic
import json
from datetime import datetime

class AnalystAgent:
    CONFIDENCE_THRESHOLD = 75

    def __init__(self, config):
        self.claude = anthropic.Anthropic(api_key=config["ANTHROPIC_API_KEY"])
        self.config = config

    async def analyze(self, ticker, regime):
        symbol = ticker.get("symbol", "")
        price = ticker.get("price", 0)
        change = ticker.get("change", 0)
        rsi = ticker.get("rsi", 50)
        prompt = (f"You are TRADO expert analyst. Regime: {regime}\n"
                  f"Symbol: {symbol} Price: ${price} Change: {change:.1f}% RSI: {rsi:.1f}\n"
                  "Respond JSON: {decision:BUY/SELL/WAIT, confidence:0-100, entry_price, stop_loss, take_profit_1, take_profit_2, position_size_pct, reason_arabic, risk_reward_ratio}")
        try:
            resp = self.claude.messages.create(
                model="claude-sonnet-4-6", max_tokens=400,
                messages=[{"role":"user","content":prompt}])
            raw = resp.content[0].text.strip()
            result = json.loads(raw)
            result["symbol"] = symbol
            result["analyzed_at"] = datetime.utcnow().isoformat()
            return result
        except Exception as e:
            return {"decision":"WAIT","confidence":0,"reason_arabic":str(e),"symbol":symbol}

    def should_execute(self, analysis):
        return (analysis.get("confidence",0) >= self.CONFIDENCE_THRESHOLD
                and analysis.get("decision") in ("BUY","SELL"))