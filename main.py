"""
TRADO Platform — FastAPI Main Application
87 AI Agents working 24/7 for Arabic traders
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger

from orchestrator.core import TRADOOrchestrator
from agents.registry import AGENT_REGISTRY, get_agent, list_all_agents
from agents._shared.base_agent import AgentContext
from config.settings import settings


app = FastAPI(
    title="TRADO Platform API",
    description="منصة تداول ذكية — 87 AI Agent يعملون 24/7",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ────────────────────────────────────────────────────────────────────

class AgentRequest(BaseModel):
    agent_id: str
    user_id: str = "demo"
    task: str
    context_data: dict = {}


class RunPipelineRequest(BaseModel):
    user_id: str = "demo"
    account_balance: float = 1000.0
    auto_execute: bool = False
    testnet: bool = True


# ── Core Routes ───────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    summary = list_all_agents()
    return {
        "name": "TRADO Platform",
        "version": "1.0.0",
        "status": "running",
        "agents": summary,
        "message": "منصة تداول ذكية 🚀 — 87 AI Agent جاهزون"
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "env": settings.app_env}


@app.get("/agents")
async def all_agents():
    """قائمة كل الـ 87 agent المتوفرة"""
    return list_all_agents()


@app.get("/agents/{department}")
async def department_agents(department: str):
    """agents قسم معين"""
    if department not in AGENT_REGISTRY:
        raise HTTPException(404, f"Department '{department}' not found")
    return {
        "department": department,
        "count": len(AGENT_REGISTRY[department]),
        "agents": list(AGENT_REGISTRY[department].keys())
    }


@app.post("/agents/run")
async def run_agent(request: AgentRequest):
    """تشغيل agent محدد بطلب"""
    try:
        agent = get_agent(request.agent_id, request.user_id)
        context = AgentContext(
            user_id=request.user_id,
            user_message=request.task,
            additional=request.context_data
        )
        response = await agent.think(context)
        return {
            "agent": agent.AGENT_NAME,
            "content": response.content,
            "cost_usd": response.cost_usd,
            "tokens": response.tokens_used,
            "processing_ms": response.processing_time_ms
        }
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.error(f"Agent error: {e}")
        raise HTTPException(500, str(e))


# ── Trading Pipeline ──────────────────────────────────────────────────────────

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
                    "executed": s.execution_result.success if s.execution_result else False,
                }
                for s in signals
            ],
            "system_status": status
        }
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        raise HTTPException(500, str(e))


@app.get("/status")
async def system_status():
    summary = list_all_agents()
    return {
        "platform": "TRADO",
        "version": "1.0.0",
        "environment": settings.app_env,
        "agents": summary,
    }


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.debug)


# ════════════════════════════════════════════════════════════════════
# Public Endpoints (للـ Landing Page)
# ════════════════════════════════════════════════════════════════════

class WaitlistRequest(BaseModel):
    email: str
    name: str = None
    country: str = None
    portfolio_size: str = None
    referral_source: str = None


@app.post("/waitlist")
async def join_waitlist(request: WaitlistRequest):
    """انضمام لقائمة الانتظار قبل الإطلاق"""
    try:
        from db.client import WaitlistDB
        result = WaitlistDB.add(
            email=request.email,
            full_name=request.name,
            country_code=request.country,
            portfolio_size=request.portfolio_size,
            referral_source=request.referral_source
        )
        count = WaitlistDB.count()
        return {
            "success": True,
            "message": "تم تسجيلك بنجاح! سنتواصل معك قريباً.",
            "waitlist_count": count,
            "position": count
        }
    except Exception as e:
        logger.error(f"Waitlist error: {e}")
        # Still return success to user (Privacy)
        return {
            "success": True,
            "message": "تم استلام طلبك."
        }


@app.get("/waitlist/count")
async def get_waitlist_count():
    """عدد الأشخاص في قائمة الانتظار (عام)"""
    try:
        from db.client import WaitlistDB
        return {"count": WaitlistDB.count()}
    except:
        return {"count": 500}    # fallback
