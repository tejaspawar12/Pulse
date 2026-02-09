"""
Phase 3 — AI insights and usage (GET /ai/insights, GET /ai/usage).
Schema-validated; cache; rate limit; fallback; request_id in response.
"""
from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user_auto
from app.models.user import User
from app.schemas.ai import AIInsightsResponse
from app.services.insights_service import get_insights
from app.utils.rate_limit import get_rate_limit_store

router = APIRouter(prefix="/ai", tags=["ai"])

INSIGHTS_RATE_LIMIT_PER_DAY = 5
SECONDS_PER_DAY = 86400


@router.get("/insights")
def get_ai_insights(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
    days: int = Query(7, ge=7, le=30, description="Period in days (7 or 30)"),
):
    """
    Phase 3: Period insights (7 or 30 days). Cached per (user, days, window_end).
    Rate limit 5/day. Fallback when AI disabled or LLM fails.
    """
    request_id = getattr(request.state, "request_id", "")
    # Normalize to 7 or 30 for cache/LLM consistency
    period_days = 7 if days <= 7 else 30
    try:
        out, cache_hit, rate_limited = get_insights(
            current_user.id,
            current_user.timezone or "UTC",
            period_days,
            db,
            request_id,
        )
    except ValueError as e:
        if str(e) == "rate_limited":
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "AI insights rate limit exceeded. Try again tomorrow.",
                    "request_id": request_id,
                },
                headers={"X-Request-Id": request_id} if request_id else None,
            )
        raise
    resp = out.model_dump()
    if request_id:
        response.headers["X-Request-Id"] = request_id
        resp["request_id"] = request_id
    return resp


@router.get("/usage")
def get_ai_usage(
    request: Request,
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
):
    """
    Phase 3: Remaining AI calls today (insights 5/day). For "AI calls remaining" in UI.
    Does not consume a call; only reports remaining.
    """
    request_id = getattr(request.state, "request_id", "")
    from app.services.stats_service import StatsService
    stats_svc = StatsService(db)
    window_end = stats_svc._get_today_date(current_user.timezone or "UTC")
    key = f"ai_insights:{current_user.id}:{window_end.isoformat()}"
    store = get_rate_limit_store()
    count = store.get_count(key, SECONDS_PER_DAY)
    remaining = max(0, INSIGHTS_RATE_LIMIT_PER_DAY - count)
    out = {
        "insights_remaining_today": remaining,
        "insights_limit_per_day": INSIGHTS_RATE_LIMIT_PER_DAY,
    }
    if request_id:
        out["request_id"] = request_id
    return out
