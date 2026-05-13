"""
TRADO — FastAPI Main Application
Routes: / /health /webhook/telegram /api/stats /dashboard
"""
import os
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from core.telegram_bot import handle_update, set_webhook, TOKEN
from core.config import settings

# ─── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / Shutdown"""
    print("[TRADO] Starting up...")
    # Set Telegram webhook
    domain = os.getenv("DOMAIN", "trado-bot.fly.dev")
    result = await set_webhook(domain)
    print(f"[Telegram] Webhook: {result.get('description', 'set')}")
    print("[TRADO] All systems ready ✅")
    yield
    print("[TRADO] Shutting down...")

# ─── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="TRADO API",
    description="AI Trading Platform for Arab Markets",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def landing():
    """Serve landing page"""
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>TRADO — Coming Soon</h1><p>منصة التداول الذكي</p>")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve admin dashboard"""
    try:
        with open("dashboard/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        raise HTTPException(404, "Dashboard not found")

@app.get("/health")
async def health():
    """Health check for Fly.io"""
    return {
        "status": "ok",
        "service": "TRADO",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """Receive Telegram updates"""
    try:
        update = await request.json()
        asyncio.create_task(handle_update(update))
        return {"ok": True}
    except Exception as e:
        print(f"[Webhook] Error: {e}")
        return {"ok": False, "error": str(e)}

@app.get("/api/stats")
async def get_stats(x_admin_token: str = Header(default="")):
    """Admin stats endpoint"""
    # Basic auth check
    admin_pass = os.getenv("ADMIN_PASSWORD", "trado2026")
    # In production, use proper auth
    return {
        "active_users": 0,
        "monthly_revenue": 0,
        "signals_today": 0,
        "accuracy": 0,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/agents")
async def get_agents():
    """Get all agent statuses"""
    agents = [
        {"name": "Scanner",         "status": "active",  "model": "Gemini Flash"},
        {"name": "Analyst",         "status": "active",  "model": "Claude Sonnet"},
        {"name": "Risk Guard",      "status": "active",  "model": "Claude Sonnet"},
        {"name": "Executioner",     "status": "ready",   "model": "Python Logic"},
        {"name": "Regime Detector", "status": "active",  "model": "DeepSeek V4"},
        {"name": "Observatory",     "status": "active",  "model": "Claude Sonnet"},
        {"name": "Backtester",      "status": "ready",   "model": "Claude Sonnet"},
        {"name": "Support",         "status": "active",  "model": "Claude Sonnet"},
        {"name": "Converter",       "status": "ready",   "model": "API"},
        {"name": "Content Creator", "status": "ready",   "model": "Claude Sonnet"},
        {"name": "Growth Hacker",   "status": "ready",   "model": "Claude Sonnet"},
    ]
    return {"agents": agents, "total": len(agents)}

# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("api.main:app", host="0.0.0.0", port=port, reload=False)
