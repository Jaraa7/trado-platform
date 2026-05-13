"""TRADO Platform - Main Entry Point"""
import asyncio
import os
from loguru import logger
from agents.scanner import ScannerAgent
from agents.analyst import AnalystAgent
from agents.risk_guard import RiskGuard
from agents.executioner import Executioner

def load_config():
    return {
        "BINANCE_API_KEY":     os.getenv("BINANCE_API_KEY",""),
        "BINANCE_API_SECRET":  os.getenv("BINANCE_API_SECRET",""),
        "BYBIT_API_KEY":       os.getenv("BYBIT_API_KEY",""),
        "BYBIT_API_SECRET":    os.getenv("BYBIT_API_SECRET",""),
        "OKX_API_KEY":         os.getenv("OKX_API_KEY",""),
        "OKX_API_SECRET":      os.getenv("OKX_API_SECRET",""),
        "ANTHROPIC_API_KEY":   os.getenv("ANTHROPIC_API_KEY",""),
        "SUPABASE_URL":        os.getenv("SUPABASE_URL",""),
        "SUPABASE_SERVICE_KEY":os.getenv("SUPABASE_SERVICE_KEY",""),
        "QDRANT_URL":          os.getenv("QDRANT_URL",""),
        "QDRANT_API_KEY":      os.getenv("QDRANT_API_KEY",""),
        "TELEGRAM_BOT_TOKEN":  os.getenv("TELEGRAM_BOT_TOKEN",""),
        "TELEGRAM_ADMIN_ID":   os.getenv("TELEGRAM_ADMIN_CHAT_ID",""),
    }

async def trading_loop(config, initial_balance=1000.0):
    scanner    = ScannerAgent(config)
    analyst    = AnalystAgent(config)
    risk_guard = RiskGuard(config, initial_balance)
    executor   = Executioner(config)
    logger.info("[TRADO] Trading loop started")

    while True:
        try:
            if risk_guard.is_hard_stop:
                logger.warning("[TRADO] Hard stop active - waiting...")
                await asyncio.sleep(300)
                continue

            # Scanner: find opportunities
            candidates = await scanner.scan()
            logger.info(f"[TRADO] {len(candidates)} candidates from scanner")

            for ticker in candidates:
                # Analyst: Claude decision
                analysis = await analyst.analyze(ticker, regime="auto")

                if not analyst.should_execute(analysis):
                    continue

                # Risk Guard: approve or reject
                approval = risk_guard.approve_trade(analysis, initial_balance)
                if not approval["approved"]:
                    logger.info(f"[TRADO] Rejected: {approval["reason"]}")
                    continue

                # Execute trade
                result = await executor.execute(analysis, approval)
                if result["success"]:
                    logger.success(f"[TRADO] Trade executed: {analysis["symbol"]}")

            await asyncio.sleep(120)  # Scan every 2 minutes

        except KeyboardInterrupt:
            logger.info("[TRADO] Shutting down...")
            await scanner.close()
            await executor.close_all()
            break
        except Exception as e:
            logger.error(f"[TRADO] Loop error: {e}")
            await asyncio.sleep(30)

if __name__ == "__main__":
    config = load_config()
    asyncio.run(trading_loop(config))