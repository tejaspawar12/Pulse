"""
Prediction service: transformation timeline from consistency and coach profile (Phase 2 Week 6).
Goal-based: uses primary_goal (strength, muscle, weight_loss, general) for milestone wording.
"""
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.user import User
from app.models.user_coach_profile import UserCoachProfile
from app.models.user_behavior_metrics import UserBehaviorMetrics
from app.models.transformation_prediction import TransformationPrediction

BASE_STRENGTH_WEEKS = 4
BASE_VISIBLE_WEEKS = 8

# Goal-specific next milestone text (timeline is driven by one goal)
MILESTONE_BY_GOAL = {
    "strength": "First strength gains",
    "muscle": "First visible muscle definition",
    "weight_loss": "First 2–3 lb drop",
    "general": "First fitness milestone",
}
DEFAULT_GOAL = "general"


def _consistency_multiplier(consistency_score: Optional[float]) -> float:
    """Higher consistency = shorter timeline (multiplier < 1)."""
    if consistency_score is None:
        return 1.6
    if consistency_score >= 80:
        return 0.8
    if consistency_score >= 60:
        return 1.0
    if consistency_score >= 40:
        return 1.3
    return 1.6


def _get_primary_goal(db: Session, user_id: UUID) -> str:
    """Return user's primary_goal from coach profile, or DEFAULT_GOAL."""
    profile = (
        db.query(UserCoachProfile)
        .filter(UserCoachProfile.user_id == user_id)
        .first()
    )
    goal = (profile.primary_goal or "").strip().lower() if profile else ""
    return goal if goal in MILESTONE_BY_GOAL else DEFAULT_GOAL


class PredictionService:
    def __init__(self, db: Session):
        self.db = db

    def compute_prediction(self, user_id: UUID) -> TransformationPrediction:
        """
        Compute transformation timeline from latest metrics and coach profile.
        Stores one row per computation (history). Returns new row with weeks_delta vs previous.
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        metrics = (
            self.db.query(UserBehaviorMetrics)
            .filter(UserBehaviorMetrics.user_id == user_id)
            .order_by(desc(UserBehaviorMetrics.computed_at))
            .first()
        )
        consistency_score = metrics.consistency_score if metrics else None
        workouts_per_week = None
        if metrics and metrics.workouts_last_14_days is not None:
            workouts_per_week = round(metrics.workouts_last_14_days / 2.0, 1)

        primary_goal = _get_primary_goal(self.db, user_id)
        mult = _consistency_multiplier(consistency_score)
        strength_gain_weeks = max(1, int(round(BASE_STRENGTH_WEEKS * mult)))
        visible_change_weeks = max(2, int(round(BASE_VISIBLE_WEEKS * mult)))
        next_milestone = MILESTONE_BY_GOAL.get(primary_goal, MILESTONE_BY_GOAL[DEFAULT_GOAL])
        next_milestone_weeks = strength_gain_weeks

        prev = (
            self.db.query(TransformationPrediction)
            .filter(TransformationPrediction.user_id == user_id)
            .order_by(desc(TransformationPrediction.computed_at))
            .first()
        )
        weeks_delta = None
        delta_reason = None
        if prev and prev.strength_gain_weeks is not None:
            weeks_delta = strength_gain_weeks - prev.strength_gain_weeks
            if weeks_delta > 0:
                delta_reason = "Consistency dropped; timeline extended"
            elif weeks_delta < 0:
                delta_reason = "Consistency improved; timeline shortened"
            else:
                delta_reason = "No change"

        row = TransformationPrediction(
            id=uuid4(),
            user_id=user_id,
            strength_gain_weeks=strength_gain_weeks,
            visible_change_weeks=visible_change_weeks,
            next_milestone=next_milestone,
            next_milestone_weeks=next_milestone_weeks,
            weeks_delta=weeks_delta,
            delta_reason=delta_reason,
            current_consistency_score=round(consistency_score, 1) if consistency_score is not None else None,
            current_workouts_per_week=workouts_per_week,
            primary_goal=primary_goal,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row
