"""
Coach service: get today's coach message with cache, entitlement, and metrics (Phase 2 Week 5 Day 3).
Uses singleton intelligence_service and llm_service.
Supports new / returning / active user context for tailored coaching (Phase 2 Week 5).
"""
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.user import User
from app.models.coach_message import CoachMessage
from app.models.coach_chat_message import CoachChatMessage
from app.models.user_behavior_metrics import UserBehaviorMetrics
from app.models.user_coach_profile import UserCoachProfile
from app.models.daily_commitment import DailyCommitment
from app.models.training_plan import TrainingPlan
from app.models.weekly_training_report import WeeklyTrainingReport
from app.services.intelligence_service import IntelligenceService
from app.services.llm_service import llm_service
from app.utils.timezone import user_today

logger = logging.getLogger(__name__)

# Days of no activity to treat user as "returning" (lapsed) rather than "active"
RETURNING_DAYS_THRESHOLD = 30
# Look back this many days to count "has user ever had workouts" (new vs returning)
NEW_USER_LOOKBACK_DAYS = 365

def _get_user_context(
    user_id: UUID, db: Session, today: date, user_tz: str
) -> dict[str, Any]:
    """
    Compute user_context for coaching: new | returning | active.
    - new: no (or negligible) workout history in last NEW_USER_LOOKBACK_DAYS.
    - returning: has history but no workout in last RETURNING_DAYS_THRESHOLD days.
    - active: has recent activity.
    Returns dict with user_context, total_workouts_last_90_days, days_since_last_workout.
    """
    # Sanitize tz for raw SQL (alphanumeric, underscore, slash only)
    safe_tz = "".join(c for c in user_tz if c.isalnum() or c in "_/") or "UTC"
    cutoff_utc = datetime.combine(
        today, datetime.min.time(), tzinfo=timezone.utc
    ) - timedelta(days=NEW_USER_LOOKBACK_DAYS)
    q = text(f"""
        WITH workout_dates AS (
            SELECT DISTINCT DATE(timezone(:tz, start_time)) AS d
            FROM workouts
            WHERE user_id = :user_id
              AND lifecycle_status = 'finalized'
              AND completion_status IN ('completed', 'partial')
              AND start_time >= :cutoff_utc
        ),
        last_date AS (
            SELECT MAX(d) AS last_d FROM workout_dates
        ),
        total_count AS (
            SELECT COUNT(*) AS n FROM workout_dates
        )
        SELECT
            (SELECT n FROM total_count) AS total_workouts,
            (SELECT last_d FROM last_date) AS last_workout_date
    """)
    try:
        row = db.execute(
            q,
            {
                "user_id": str(user_id),
                "tz": safe_tz,
                "cutoff_utc": cutoff_utc,
            },
        ).first()
    except Exception as e:
        logger.warning("_get_user_context query failed: %s", e)
        return {
            "user_context": "active",
            "total_workouts_last_90_days": 0,
            "days_since_last_workout": None,
        }
    if not row:
        return {
            "user_context": "new",
            "total_workouts_last_90_days": 0,
            "days_since_last_workout": None,
        }
    total = int(row.total_workouts) if row.total_workouts is not None else 0
    last_d = row.last_workout_date
    if total == 0 or last_d is None:
        return {
            "user_context": "new",
            "total_workouts_last_90_days": total,
            "days_since_last_workout": None,
        }
    days_since = (today - last_d).days
    if days_since > RETURNING_DAYS_THRESHOLD:
        context = "returning"
    else:
        context = "active"
    return {
        "user_context": context,
        "total_workouts_last_90_days": total,
        "days_since_last_workout": days_since,
    }


def _build_facts_json(
    metrics: Optional[UserBehaviorMetrics],
    profile: Optional[UserCoachProfile],
    user_context_dict: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Build facts dict for LLM from metrics, profile, and user context (new/returning/active)."""
    facts: dict[str, Any] = {}
    if user_context_dict:
        facts["user_context"] = user_context_dict.get("user_context", "active")
        facts["total_workouts_last_90_days"] = user_context_dict.get("total_workouts_last_90_days", 0)
        facts["days_since_last_workout"] = user_context_dict.get("days_since_last_workout")
    if profile:
        facts["primary_goal"] = profile.primary_goal
        facts["experience_level"] = profile.experience_level
        facts["target_days_per_week"] = profile.target_days_per_week
        facts["target_session_minutes"] = profile.target_session_minutes
        facts["preferred_workout_time"] = profile.preferred_workout_time
        facts["available_equipment"] = profile.available_equipment
    if metrics:
        facts["consistency_score"] = metrics.consistency_score
        facts["dropout_risk"] = metrics.dropout_risk
        facts["burnout_risk"] = metrics.burnout_risk
        facts["momentum_trend"] = metrics.momentum_trend
        facts["adherence_type"] = metrics.adherence_type
        facts["workouts_last_7_days"] = metrics.workouts_last_7_days
        facts["workouts_last_14_days"] = metrics.workouts_last_14_days
        facts["primary_training_mistake_key"] = metrics.primary_training_mistake_key
        facts["primary_training_mistake_label"] = metrics.primary_training_mistake_label
        facts["weekly_focus_key"] = metrics.weekly_focus_key
        facts["weekly_focus_label"] = metrics.weekly_focus_label
        facts["reasons"] = metrics.reasons
    return facts


def _get_recent_workouts(
    user_id: UUID, db: Session, user_tz: str, today: date, days: int = 14
) -> list[dict[str, Any]]:
    """Return recent workouts (date, duration_minutes, total_volume, exercises) for the last N days, newest first."""
    safe_tz = "".join(c for c in user_tz if c.isalnum() or c in "_/") or "UTC"
    start_date = today - timedelta(days=days - 1)
    q = text("""
        SELECT
            DATE(timezone(:tz, w.start_time)) AS workout_date,
            w.duration_minutes,
            COALESCE(SUM(CASE WHEN ws.set_type = 'working' THEN COALESCE(ws.weight, 0)::numeric * COALESCE(ws.reps, 0) ELSE 0 END), 0)::float AS total_volume,
            array_remove(array_agg(DISTINCT el.name), NULL) AS exercise_names
        FROM workouts w
        LEFT JOIN workout_exercises we ON we.workout_id = w.id
        LEFT JOIN exercise_library el ON el.id = we.exercise_id
        LEFT JOIN workout_sets ws ON ws.workout_exercise_id = we.id
        WHERE w.user_id = :user_id
          AND w.lifecycle_status = 'finalized'
          AND w.completion_status IN ('completed', 'partial')
          AND DATE(timezone(:tz, w.start_time)) >= :start_date
          AND DATE(timezone(:tz, w.start_time)) <= :end_date
        GROUP BY w.id, w.start_time, w.duration_minutes
        ORDER BY workout_date DESC
    """)
    try:
        rows = db.execute(
            q,
            {
                "user_id": str(user_id),
                "tz": safe_tz,
                "start_date": start_date,
                "end_date": today,
            },
        ).fetchall()
    except Exception as e:
        logger.warning("_get_recent_workouts failed: %s", e)
        return []
    out = []
    for row in rows:
        exercises = list(row.exercise_names) if row.exercise_names else []
        out.append({
            "workout_date": str(row.workout_date),
            "duration_minutes": row.duration_minutes,
            "total_volume": round(float(row.total_volume or 0), 1),
            "exercises": exercises,
        })
    return out


def _get_recent_commitments(
    user_id: UUID, db: Session, today: date, days: int = 14
) -> list[dict[str, Any]]:
    """Return recent commitments (commitment_date, status, completed) for the last N days, newest first."""
    start_date = today - timedelta(days=days - 1)
    rows = (
        db.query(DailyCommitment)
        .filter(
            DailyCommitment.user_id == user_id,
            DailyCommitment.commitment_date >= start_date,
            DailyCommitment.commitment_date <= today,
        )
        .order_by(DailyCommitment.commitment_date.desc())
        .all()
    )
    return [
        {
            "commitment_date": str(r.commitment_date),
            "status": r.status,
            "completed": r.completed,
        }
        for r in rows
    ]


def _get_training_plan(user_id: UUID, db: Session) -> Optional[dict[str, Any]]:
    """Return current training plan for the user, or None."""
    plan = (
        db.query(TrainingPlan)
        .filter(TrainingPlan.user_id == user_id)
        .first()
    )
    if not plan:
        return None
    return {
        "days_per_week": plan.days_per_week,
        "session_duration_target": plan.session_duration_target,
        "split_type": plan.split_type,
        "volume_multiplier": plan.volume_multiplier,
        "progression_type": plan.progression_type,
        "auto_adjust_enabled": plan.auto_adjust_enabled,
        "deload_week_frequency": plan.deload_week_frequency,
    }


def _get_last_weekly_report(user_id: UUID, db: Session) -> Optional[dict[str, Any]]:
    """Return last weekly training report summary, or None."""
    report = (
        db.query(WeeklyTrainingReport)
        .filter(WeeklyTrainingReport.user_id == user_id)
        .order_by(WeeklyTrainingReport.week_start.desc())
        .first()
    )
    if not report:
        return None
    return {
        "week_start": str(report.week_start),
        "week_end": str(report.week_end),
        "workouts_count": report.workouts_count,
        "total_volume_kg": report.total_volume_kg,
        "volume_delta_pct": report.volume_delta_pct,
        "avg_session_duration": report.avg_session_duration,
        "primary_training_mistake_label": report.primary_training_mistake_label,
        "weekly_focus_label": report.weekly_focus_label,
        "narrative": report.narrative,
        "status": report.status,
    }


def _user_body_facts(user: Optional[User], today: date) -> dict[str, Any]:
    """Build user body/personal facts for coach (weight, height, age, gender)."""
    out: dict[str, Any] = {}
    if not user:
        return out
    if user.weight_kg is not None:
        out["user_weight_kg"] = round(user.weight_kg, 1)
    if user.height_cm is not None:
        out["user_height_cm"] = round(user.height_cm, 1)
    if user.date_of_birth is not None:
        out["user_date_of_birth"] = str(user.date_of_birth)
        age = today.year - user.date_of_birth.year - (
            (today.month, today.day) < (user.date_of_birth.month, user.date_of_birth.day)
        )
        out["user_age_years"] = max(0, age)
    if user.gender:
        out["user_gender"] = user.gender
    return out


def _build_full_facts_json(
    metrics: Optional[UserBehaviorMetrics],
    profile: Optional[UserCoachProfile],
    user_context_dict: Optional[dict[str, Any]],
    user_id: UUID,
    db: Session,
    user_tz: str,
    today: date,
) -> dict[str, Any]:
    """Build full facts for coach: metrics, profile, context, user body, recent workouts, commitments, plan, last report."""
    facts = _build_facts_json(metrics, profile, user_context_dict)
    user = db.query(User).filter(User.id == user_id).first()
    facts.update(_user_body_facts(user, today))
    facts["recent_workouts"] = _get_recent_workouts(user_id, db, user_tz, today, days=14)
    facts["recent_commitments"] = _get_recent_commitments(user_id, db, today, days=14)
    plan = _get_training_plan(user_id, db)
    facts["training_plan"] = plan
    report = _get_last_weekly_report(user_id, db)
    facts["last_weekly_report"] = report
    return facts


def get_today_message(user_id: UUID, db: Session) -> dict[str, Any]:
    """
    Get today's coach message for the user.
    - Load user; if no user return error state.
    - If not Pro/trial: return free-tier message (cached).
    - If cached (CoachMessage for today with source in ai/free_tier): return cached.
    - If Bedrock not ready: return unavailable.
    - Else: compute metrics, build facts_json, call LLM, cache if ai, return.
    Caller is responsible for commit after this call if new rows were added.
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"source": "error", "error": "user_not_found"}

        tz = (user.timezone or "Asia/Kolkata").strip() or "Asia/Kolkata"
        today = user_today(tz)

        # All users get AI coach (no Pro gate)
        cached = (
            db.query(CoachMessage)
            .filter(
                CoachMessage.user_id == user_id,
                CoachMessage.message_date == today,
                CoachMessage.source == "ai",
            )
            .first()
        )
        if cached:
            out = dict(cached.payload or {})
            out["source"] = cached.source
            out["generated_at"] = cached.generated_at.isoformat() if cached.generated_at else None
            out["model_id"] = cached.model_id
            out["ai_lite_used"] = cached.ai_lite_used
            return out

        # Bedrock check
        if not llm_service.bedrock_ready:
            logger.warning("Coach unavailable: Bedrock not ready (BEDROCK_MODEL_ID_DAILY unset or init failed).")
            return {"source": "unavailable", "retry_after_seconds": 60}

        # Ensure metrics for today
        intel = IntelligenceService(db)
        metrics = (
            db.query(UserBehaviorMetrics)
            .filter(
                UserBehaviorMetrics.user_id == user_id,
                UserBehaviorMetrics.metrics_date == today,
            )
            .first()
        )
        if not metrics:
            metrics = intel.compute_metrics(user_id, metrics_date=today)

        profile = (
            db.query(UserCoachProfile)
            .filter(UserCoachProfile.user_id == user_id)
            .first()
        )
        user_context = _get_user_context(user_id, db, today, tz)
        facts_json = _build_full_facts_json(
            metrics, profile, user_context, user_id, db, tz, today
        )

        result = llm_service.generate_coach_message(
            user_id=user_id,
            facts_json=facts_json,
            usage_date=today,
            db=db,
        )

        if result.get("source") == "unavailable":
            return result

        if result.get("source") == "ai":
            payload = {
                "coach_message": result["coach_message"],
                "quick_replies": result["quick_replies"],
                "one_action_step": result["one_action_step"],
            }
            now = datetime.now(timezone.utc)
            # Upsert: replace any existing row for today (e.g. was free_tier or stale)
            existing = (
                db.query(CoachMessage)
                .filter(
                    CoachMessage.user_id == user_id,
                    CoachMessage.message_date == today,
                )
                .first()
            )
            if existing:
                existing.source = "ai"
                existing.generated_at = now
                existing.model_id = result.get("model_id")
                existing.ai_lite_used = result.get("ai_lite_used", False)
                existing.payload = payload
            else:
                db.add(
                    CoachMessage(
                        user_id=user_id,
                        message_date=today,
                        source="ai",
                        generated_at=now,
                        model_id=result.get("model_id"),
                        ai_lite_used=result.get("ai_lite_used", False),
                        payload=payload,
                    )
                )
            db.flush()
            return {
                "source": "ai",
                "coach_message": result["coach_message"],
                "quick_replies": result["quick_replies"],
                "one_action_step": result["one_action_step"],
                "generated_at": now.isoformat(),
                "model_id": result.get("model_id"),
                "ai_lite_used": result.get("ai_lite_used", False),
            }

        return result
    except Exception as e:
        logger.exception("get_today_message failed for user %s: %s", user_id, e)
        return {"source": "unavailable", "retry_after_seconds": 60}


def get_chat_history(user_id: UUID, db: Session, limit: int = 50) -> list[dict[str, Any]]:
    """Return last N chat messages for the user, oldest first. Each dict: role, content, created_at (iso)."""
    rows = (
        db.query(CoachChatMessage)
        .filter(CoachChatMessage.user_id == user_id)
        .order_by(CoachChatMessage.created_at.asc())
        .limit(limit)
        .all()
    )
    return [
        {
            "role": r.role,
            "content": r.content or "",
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


def delete_old_coach_chat_messages(db: Session, older_than_days: int) -> int:
    """Delete coach chat messages older than the given days (UTC). Returns count deleted. Use 0 to skip."""
    if older_than_days <= 0:
        return 0
    cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
    deleted = db.query(CoachChatMessage).filter(CoachChatMessage.created_at < cutoff).delete()
    logger.info("Coach chat cleanup: deleted %d message(s) older than %d days", deleted, older_than_days)
    return deleted


def send_chat_message(user_id: UUID, message: str, db: Session) -> Optional[str]:
    """
    Append user message, call LLM with facts + history, save assistant reply, return reply text.
    Uses same real data (metrics, profile, user context) as today's coach message.
    """
    if not (message or "").strip():
        return None
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        tz = (user.timezone or "Asia/Kolkata").strip() or "Asia/Kolkata"
        today = user_today(tz)

        if not llm_service.bedrock_ready:
            logger.warning("Coach chat: Bedrock not ready")
            return "Coach is temporarily unavailable. Please try again in a minute."

        intel = IntelligenceService(db)
        metrics = (
            db.query(UserBehaviorMetrics)
            .filter(
                UserBehaviorMetrics.user_id == user_id,
                UserBehaviorMetrics.metrics_date == today,
            )
            .first()
        )
        if not metrics:
            metrics = intel.compute_metrics(user_id, metrics_date=today)
        profile = (
            db.query(UserCoachProfile)
            .filter(UserCoachProfile.user_id == user_id)
            .first()
        )
        user_context = _get_user_context(user_id, db, today, tz)
        facts_json = _build_full_facts_json(
            metrics, profile, user_context, user_id, db, tz, today
        )

        # History before adding current message (last 30 turns)
        history_rows = (
            db.query(CoachChatMessage)
            .filter(CoachChatMessage.user_id == user_id)
            .order_by(CoachChatMessage.created_at.asc())
            .limit(30)
            .all()
        )
        history = [{"role": r.role, "content": r.content or ""} for r in history_rows]

        # Save user message
        db.add(
            CoachChatMessage(
                user_id=user_id,
                role="user",
                content=(message or "").strip(),
            )
        )
        db.flush()

        reply, _, _ = llm_service.generate_chat_reply(
            user_id=user_id,
            facts_json=facts_json,
            history=history,
            user_message=(message or "").strip(),
            usage_date=today,
            db=db,
        )
        if reply:
            db.add(
                CoachChatMessage(
                    user_id=user_id,
                    role="assistant",
                    content=reply,
                )
            )
            db.flush()
            return reply
        return "Sorry, I couldn't generate a reply right now. Please try again."
    except Exception as e:
        logger.exception("send_chat_message failed for user %s: %s", user_id, e)
        return "Something went wrong. Please try again."
