"""مسارات /nervous/* — كلها تتطلب تسجيل دخول."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth.service import get_current_user
from nervous.goals import GoalEngine, Goal
from nervous.market import MarketResearch
from nervous.performance import PerformanceTracker
from nervous.conflicts import ConflictChecker

router = APIRouter(prefix="/nervous", tags=["nervous"])


class GoalIn(BaseModel):
    id: str = Field(..., pattern=r"^[a-z0-9_\-]{2,64}$")
    title: str
    impact: float = Field(..., ge=1, le=10)
    urgency: float = Field(..., ge=1, le=10)
    effort: float = Field(..., ge=1, le=10)
    confidence: float = Field(7, ge=1, le=10)
    metric: str = ""
    depends_on: list[str] = []
    notes: str = ""


@router.get("/goals")
async def goals_ranked(user: dict = Depends(get_current_user)):
    e = GoalEngine()
    return {"tiers": {k: [g.__dict__ | {"score": g.score} for g in v] for k, v in e.tiers().items()},
            "next": (e.next_action().__dict__ if e.next_action() else None)}


@router.post("/goals")
async def goals_add(body: GoalIn, user: dict = Depends(get_current_user)):
    e = GoalEngine()
    try:
        g = e.add(Goal(**body.model_dump()))
    except ValueError as ex:
        raise HTTPException(400, str(ex))
    e.save()
    return g.__dict__ | {"score": g.score}


@router.patch("/goals/{goal_id}/status")
async def goals_status(goal_id: str, status: str, user: dict = Depends(get_current_user)):
    if status not in ("open", "doing", "done", "dropped"):
        raise HTTPException(400, "status غير صالح")
    e = GoalEngine()
    try:
        g = e.update(goal_id, status=status)
    except KeyError as ex:
        raise HTTPException(404, str(ex))
    e.save()
    return g.__dict__


@router.get("/market/brief")
async def market_brief(interval: str = "1h", user: dict = Depends(get_current_user)):
    return await MarketResearch().brief(interval=interval)


@router.get("/performance")
async def performance(days: int = 30, user: dict = Depends(get_current_user)):
    return PerformanceTracker.from_supabase(days=days).report()


@router.get("/conflicts")
async def conflicts(user: dict = Depends(get_current_user)):
    return ConflictChecker().run()
