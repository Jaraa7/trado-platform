"""
TRADO Platform — FastAPI Main Application
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import asyncio
from loguru import logger

from orchestrator.core import TRADOOrchestrator
from config.settings import settings

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="TRADO Platform API",
    description="منصة تداول ذكية — 87 AI Agent يعملون 24/7",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Models ────────────────────────────────────────────────────────────────────

class RunPipelineRequest(BaseModel):
    user_id: str = "demo"
    account_balance: float = 1000.0
    auto_execute: bool = False
    testnet: bool = True


class AnalyzeRequest(BaseModel):
    user_id: str = "demo"
    symbol: str
    question: str = "حلل هذا الزوج"


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "name": "TRADO Platform",
        "version": "1.0.0",
        "status": "running",
        "agents": 87,
        "message": "منصة تداول ذكية 🚀"
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "env": settings.app_env}


@app.post("/pipeline/run")
async def run_pipeline(request: RunPipelineRequest):
    """تشغيل pipeline التداول الكامل"""
    try:
        orchestrator = TRADOOrchestrator(user_id=request.user_id)
        signals = await orchestrator.run_trading_pipeline(
            account_balance=request.account_balance,
            auto_execute=request.auto_execute,
            testnet=request.testnet
        )

        status = await orchestrator.get_system_status()

        return {
            "success": True,
            "signals_found": len(signals),
            "signals": [
                {
                    "symbol": s.symbol,
                    "direction": s.direction,
                    "entry": s.entry_price,
                    "stop_loss": s.stop_loss,
                    "take_profit": s.take_profit,
                    "confidence": s.confidence,
                    "risk_approved": s.risk_decision.approved if s.risk_decision else False,
                    "executed": s.execution_result.success if s.execution_result else False,
                    "timestamp": s.timestamp
                }
                for s in signals
            ],
            "system_status": status
        }
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze")
async def analyze_symbol(request: AnalyzeRequest):
    """تحليل فني لزوج عملات"""
    try:
        from agents.trading.analyst.agent import AnalystMaster
        from agents._shared.base_agent import AgentContext

        analyst = AnalystMaster(user_id=request.user_id)
        context = AgentContext(
            user_id=request.user_id,
            user_message=f"{request.question} — {request.symbol}"
        )
        response = await analyst.think(context)

        return {
            "symbol": request.symbol,
            "analysis": response.content,
            "cost_usd": response.cost_usd,
            "processing_ms": response.processing_time_ms
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def system_status():
    """حالة النظام"""
    return {
        "platform": "TRADO",
        "version": "1.0.0",
        "environment": settings.app_env,
        "agents_available": {
            "trading": 15,
            "engineering": 10,
            "security": 7,
            "financial": 12,
            "customer": 11,
            "marketing": 12,
            "design": 7,
            "product": 7,
            "operations": 6,
            "total": 87
        },
        "implemented": {
            "scanner_pro": True,
            "analyst_master": True,
            "risk_guardian": True,
            "executioner_pro": True,
            "observatory": True,
            "orchestrator": True
        }
    }


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
