"""
Coach API: today's message, respond, status, metrics, profile (Phase 2 Week 5 Day 4).
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user_auto
from app.config.settings import settings
from app.models.user import User
from app.models.coach_message import CoachMessage
from app.models.user_behavior_metrics import UserBehaviorMetrics
from app.models.user_coach_profile import UserCoachProfile
from app.models.accountability_event import AccountabilityEvent
from app.schemas.coach import CoachProfileOut, CoachProfileUpdate
from app.services.coach_service import get_today_message, get_chat_history, send_chat_message
from app.services.intelligence_service import IntelligenceService
from app.utils.timezone import user_today

router = APIRouter(prefix="/coach", tags=["coach"])


@router.get("/profile", response_model=CoachProfileOut)
def get_coach_profile(
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
) -> CoachProfileOut:
    """Get current user's coach profile (goal, preferences). Returns defaults if no profile yet."""
    profile = (
        db.query(UserCoachProfile)
        .filter(UserCoachProfile.user_id == current_user.id)
        .first()
    )
    if not profile:
        return CoachProfileOut(primary_goal=None, experience_level=None, target_days_per_week=None, target_session_minutes=None)
    return CoachProfileOut(
        primary_goal=profile.primary_goal,
        experience_level=profile.experience_level,
        target_days_per_week=profile.target_days_per_week,
        target_session_minutes=profile.target_session_minutes,
    )


@router.patch("/profile", response_model=CoachProfileOut)
def update_coach_profile(
    body: CoachProfileUpdate,
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
) -> CoachProfileOut:
    """Update coach profile (e.g. primary_goal). Creates profile if missing."""
    profile = (
        db.query(UserCoachProfile)
        .filter(UserCoachProfile.user_id == current_user.id)
        .first()
    )
    if not profile:
        profile = UserCoachProfile(user_id=current_user.id)
        db.add(profile)
        db.flush()
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return CoachProfileOut(
        primary_goal=profile.primary_goal,
        experience_level=profile.experience_level,
        target_days_per_week=profile.target_days_per_week,
        target_session_minutes=profile.target_session_minutes,
    )


@router.get("/today")
def get_coach_today(
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Get today's coach message. Response shape depends on source:
    - ai: coach_message, quick_replies, one_action_step, generated_at, model_id, ai_lite_used
    - free_tier: coach_message, quick_replies, one_action_step, is_free_tier
    - unavailable: retry_after_seconds
    """
    result = get_today_message(current_user.id, db)
    db.commit()
    # Omit debug fields for non-ai
    if result.get("source") == "ai":
        return {
            "source": "ai",
            "coach_message": result.get("coach_message"),
            "quick_replies": result.get("quick_replies", []),
            "one_action_step": result.get("one_action_step"),
            "generated_at": result.get("generated_at"),
            "model_id": result.get("model_id"),
            "ai_lite_used": result.get("ai_lite_used", False),
        }
    if result.get("source") == "free_tier":
        return {
            "source": "free_tier",
            "is_free_tier": True,
            "coach_message": result.get("coach_message"),
            "quick_replies": result.get("quick_replies", []),
            "one_action_step": result.get("one_action_step"),
        }
    if result.get("source") == "unavailable":
        return {
            "source": "unavailable",
            "retry_after_seconds": result.get("retry_after_seconds", 60),
        }
    if result.get("source") == "error":
        raise HTTPException(status_code=404, detail=result.get("error", "Not found"))
    return result


@router.get("/chat")
def get_coach_chat(
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
) -> list[dict[str, Any]]:
    """Get chat history for the coach conversation (oldest first)."""
    return get_chat_history(current_user.id, db, limit=limit)


@router.post("/chat")
def post_coach_chat(
    body: dict[str, str],
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Send a message to the coach and get a reply. Uses only real stored data (metrics, profile, history)."""
    message = (body or {}).get("message", "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")
    reply = send_chat_message(current_user.id, message, db)
    db.commit()
    return {"reply": reply or ""}


@router.post("/respond", status_code=204)
def coach_respond(
    body: dict[str, str],
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
) -> None:
    """
    Record a reply to today's coach message. Only recorded if today's cached
    CoachMessage has source == "ai". Otherwise 204 no-op.
    """
    reply_text = (body or {}).get("reply_text", "").strip()
    tz = (current_user.timezone or "Asia/Kolkata").strip() or "Asia/Kolkata"
    today = user_today(tz)
    msg = (
        db.query(CoachMessage)
        .filter(
            CoachMessage.user_id == current_user.id,
            CoachMessage.message_date == today,
        )
        .first()
    )
    if not msg or msg.source != "ai":
        return
    event = AccountabilityEvent(
        user_id=current_user.id,
        commitment_id=None,
        event_type="coach_reply",
        event_data={"reply_text": reply_text},
    )
    db.add(event)
    db.commit()


@router.get("/status")
def get_coach_status(
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Current metrics summary: consistency_score, momentum_trend, dropout_risk, etc."""
    tz = (current_user.timezone or "Asia/Kolkata").strip() or "Asia/Kolkata"
    today = user_today(tz)
    m = (
        db.query(UserBehaviorMetrics)
        .filter(
            UserBehaviorMetrics.user_id == current_user.id,
            UserBehaviorMetrics.metrics_date == today,
        )
        .first()
    )
    if not m:
        return {
            "consistency_score": None,
            "momentum_trend": None,
            "dropout_risk": None,
            "burnout_risk": None,
            "primary_training_mistake_key": None,
            "weekly_focus_key": None,
        }
    return {
        "consistency_score": m.consistency_score,
        "momentum_trend": m.momentum_trend,
        "dropout_risk": m.dropout_risk,
        "burnout_risk": m.burnout_risk,
        "primary_training_mistake_key": m.primary_training_mistake_key,
        "primary_training_mistake_label": m.primary_training_mistake_label,
        "weekly_focus_key": m.weekly_focus_key,
        "weekly_focus_label": m.weekly_focus_label,
    }


@router.get("/metrics")
def get_coach_metrics(
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=90),
) -> list[dict[str, Any]]:
    """Behavior metrics for the last N days (for charts/history)."""
    tz = (current_user.timezone or "Asia/Kolkata").strip() or "Asia/Kolkata"
    today = user_today(tz)
    from datetime import timedelta
    start = today - timedelta(days=days - 1)
    rows = (
        db.query(UserBehaviorMetrics)
        .filter(
            UserBehaviorMetrics.user_id == current_user.id,
            UserBehaviorMetrics.metrics_date >= start,
            UserBehaviorMetrics.metrics_date <= today,
        )
        .order_by(UserBehaviorMetrics.metrics_date.desc())
        .all()
    )
    return [
        {
            "metrics_date": str(r.metrics_date),
            "consistency_score": r.consistency_score,
            "dropout_risk": r.dropout_risk,
            "burnout_risk": r.burnout_risk,
            "momentum_trend": r.momentum_trend,
            "adherence_type": r.adherence_type,
            "workouts_last_7_days": r.workouts_last_7_days,
            "workouts_last_14_days": r.workouts_last_14_days,
            "primary_training_mistake_key": r.primary_training_mistake_key,
            "weekly_focus_key": r.weekly_focus_key,
            "reasons": r.reasons,
        }
        for r in rows
    ]


@router.post("/recompute-metrics")
def recompute_metrics(
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Recompute today's behavior metrics for the current user (dev/testing).
    In production, gate or remove this endpoint.
    """
    if settings.ENVIRONMENT != "development":
        raise HTTPException(status_code=403, detail="Only available in development")
    intel = IntelligenceService(db)
    metrics = intel.compute_metrics(current_user.id)
    db.commit()
    return {
        "metrics_date": str(metrics.metrics_date),
        "consistency_score": metrics.consistency_score,
        "dropout_risk": metrics.dropout_risk,
        "burnout_risk": metrics.burnout_risk,
        "momentum_trend": metrics.momentum_trend,
        "adherence_type": metrics.adherence_type,
        "workouts_last_7_days": metrics.workouts_last_7_days,
        "workouts_last_14_days": metrics.workouts_last_14_days,
        "primary_training_mistake_key": metrics.primary_training_mistake_key,
        "weekly_focus_key": metrics.weekly_focus_key,
        "reasons": metrics.reasons,
    }
