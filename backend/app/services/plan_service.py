"""
Plan service: training plan and weekly adjustments (Phase 2 Week 7).
Week 7 only adjusts volume_multiplier; days_per_week auto-changes are deferred.
"""
from datetime import date, timedelta
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.user import User
from app.models.user_coach_profile import UserCoachProfile
from app.models.user_behavior_metrics import UserBehaviorMetrics
from app.models.training_plan import TrainingPlan
from app.models.weekly_plan_adjustment import WeeklyPlanAdjustment
from app.utils.timezone import user_today

MIN_VOLUME = 0.6
MAX_VOLUME = 1.2
DEFAULT_DAYS_PER_WEEK = 3
DEFAULT_SESSION_MINUTES = 45

# Goal-aware defaults when creating a plan (used when profile has no target_days_per_week)
GOAL_DEFAULT_DAYS = {"strength": 3, "muscle": 4, "weight_loss": 3, "general": 3}
GOAL_DEFAULT_SPLIT = {"strength": "full_body", "muscle": "upper_lower", "weight_loss": "full_body", "general": "full_body"}

# Stable keys (do not change without updating plan logic)
TRIGGER_BURNOUT = "burnout"
TRIGGER_SLIPPING = "slipping"
TRIGGER_MOMENTUM_UP = "momentum_up"
PRIMARY_MISTAKE_VOLUME_DROP = "volume_drop"

# Allowed values for preferences (validate on PATCH)
ALLOWED_SPLIT_TYPES = frozenset({"full_body", "upper_lower", "push_pull_legs"})
ALLOWED_PROGRESSION_TYPES = frozenset({"linear", "wave", "autoregulated"})


def _sanitize_timezone(tz: str) -> str:
    import re
    if not tz or not re.match(r"^[A-Za-z0-9_/+-]+$", tz):
        return "UTC"
    return tz


def _clamp_volume(value: float) -> float:
    return round(min(MAX_VOLUME, max(MIN_VOLUME, value)), 2)


def _metrics_snapshot(metrics: Optional[UserBehaviorMetrics]) -> Optional[dict[str, Any]]:
    if not metrics:
        return None
    return {
        "consistency_score": round(metrics.consistency_score, 1) if metrics.consistency_score is not None else None,
        "burnout_risk": metrics.burnout_risk,
        "momentum_trend": metrics.momentum_trend,
    }


class PlanService:
    def __init__(self, db: Session):
        self.db = db

    def get_current_plan(self, user_id: UUID) -> Optional[TrainingPlan]:
        return self.db.query(TrainingPlan).filter(TrainingPlan.user_id == user_id).first()

    def create_plan(self, user_id: UUID) -> TrainingPlan:
        existing = self.get_current_plan(user_id)
        if existing:
            return existing
        profile = self.db.query(UserCoachProfile).filter(UserCoachProfile.user_id == user_id).first()
        goal = (profile.primary_goal or "").strip().lower() if profile else ""
        if goal not in GOAL_DEFAULT_DAYS:
            goal = "general"
        days = (profile.target_days_per_week if profile else None) or GOAL_DEFAULT_DAYS.get(goal, DEFAULT_DAYS_PER_WEEK)
        minutes = (profile.target_session_minutes if profile else None) or DEFAULT_SESSION_MINUTES
        split_type = GOAL_DEFAULT_SPLIT.get(goal, "full_body")
        plan = TrainingPlan(
            id=uuid4(),
            user_id=user_id,
            days_per_week=days,
            session_duration_target=minutes,
            split_type=split_type,
            volume_multiplier=1.0,
            progression_type="linear",
            auto_adjust_enabled=False,
            deload_week_frequency=4,
        )
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def update_preferences(
        self,
        user_id: UUID,
        user: User,
        *,
        days_per_week: Optional[int] = None,
        session_duration_target: Optional[int] = None,
        split_type: Optional[str] = None,
        progression_type: Optional[str] = None,
        deload_week_frequency: Optional[int] = None,
        auto_adjust_enabled: Optional[bool] = None,
    ) -> TrainingPlan:
        plan = self.get_current_plan(user_id)
        if not plan:
            raise ValueError("No plan found")
        if split_type is not None and split_type not in ALLOWED_SPLIT_TYPES:
            raise ValueError(
                f"split_type must be one of {sorted(ALLOWED_SPLIT_TYPES)}"
            )
        if progression_type is not None and progression_type not in ALLOWED_PROGRESSION_TYPES:
            raise ValueError(
                f"progression_type must be one of {sorted(ALLOWED_PROGRESSION_TYPES)}"
            )
        if days_per_week is not None:
            plan.days_per_week = days_per_week
        if session_duration_target is not None:
            plan.session_duration_target = session_duration_target
        if split_type is not None:
            plan.split_type = split_type
        if progression_type is not None:
            plan.progression_type = progression_type
        if deload_week_frequency is not None:
            plan.deload_week_frequency = deload_week_frequency
        if auto_adjust_enabled is not None:
            plan.auto_adjust_enabled = auto_adjust_enabled
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def get_this_week_start(self, user_id: UUID) -> Optional[date]:
        """Return Monday of the current week (user's today in their TZ). None if user not found."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        tz = _sanitize_timezone(user.timezone or "Asia/Kolkata")
        try:
            today = user_today(tz)
        except Exception:
            today = user_today("UTC")
        return today - timedelta(days=today.weekday())

    def get_this_week_adjustment(self, user_id: UUID) -> Optional[WeeklyPlanAdjustment]:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        tz = _sanitize_timezone(user.timezone or "Asia/Kolkata")
        try:
            today = user_today(tz)
        except Exception:
            today = user_today("UTC")
        this_monday = today - timedelta(days=today.weekday())
        return (
            self.db.query(WeeklyPlanAdjustment)
            .filter(
                WeeklyPlanAdjustment.user_id == user_id,
                WeeklyPlanAdjustment.week_start == this_monday,
            )
            .first()
        )

    def get_adjustment_history(self, user_id: UUID, limit: int = 12) -> list[WeeklyPlanAdjustment]:
        return (
            self.db.query(WeeklyPlanAdjustment)
            .filter(WeeklyPlanAdjustment.user_id == user_id)
            .order_by(desc(WeeklyPlanAdjustment.week_start))
            .limit(limit)
            .all()
        )

    def compute_weekly_adjustment(self, user_id: UUID, week_start: date) -> Optional[WeeklyPlanAdjustment]:
        plan = self.get_current_plan(user_id)
        if not plan or not plan.auto_adjust_enabled:
            return None
        existing = (
            self.db.query(WeeklyPlanAdjustment)
            .filter(
                WeeklyPlanAdjustment.plan_id == plan.id,
                WeeklyPlanAdjustment.week_start == week_start,
            )
            .first()
        )
        if existing:
            return existing
        metrics = (
            self.db.query(UserBehaviorMetrics)
            .filter(UserBehaviorMetrics.user_id == user_id)
            .order_by(desc(UserBehaviorMetrics.computed_at))
            .first()
        )
        last_adjustment = (
            self.db.query(WeeklyPlanAdjustment)
            .filter(WeeklyPlanAdjustment.plan_id == plan.id, WeeklyPlanAdjustment.week_start < week_start)
            .order_by(desc(WeeklyPlanAdjustment.week_start))
            .first()
        )
        momentum_threshold = 80
        if last_adjustment:
            if last_adjustment.is_deload:
                momentum_threshold = 999
            elif (
                last_adjustment.previous_volume_multiplier is not None
                and last_adjustment.new_volume_multiplier is not None
                and last_adjustment.new_volume_multiplier < last_adjustment.previous_volume_multiplier
            ):
                momentum_threshold = 85
        if metrics and metrics.burnout_risk == "high":
            return self._create_deload_adjustment(plan, TRIGGER_BURNOUT, week_start, metrics)
        if metrics and getattr(metrics, "primary_training_mistake_key", None) == PRIMARY_MISTAKE_VOLUME_DROP:
            return self._create_volume_reduction(plan, TRIGGER_SLIPPING, week_start, metrics)
        if momentum_threshold >= 999:
            return None
        if metrics and getattr(metrics, "momentum_trend", None) == "rising":
            consistency = metrics.consistency_score or 0
            if consistency >= momentum_threshold:
                return self._create_volume_increase(plan, TRIGGER_MOMENTUM_UP, week_start, metrics)
        return None

    def _create_deload_adjustment(
        self,
        plan: TrainingPlan,
        trigger_reason: str,
        week_start: date,
        metrics: Optional[UserBehaviorMetrics],
    ) -> Optional[WeeklyPlanAdjustment]:
        prev = plan.volume_multiplier or 1.0
        new_vol = _clamp_volume(prev * 0.6)
        if round(new_vol, 2) == round(prev, 2):
            return None
        plan.volume_multiplier = new_vol
        adj = WeeklyPlanAdjustment(
            id=uuid4(),
            user_id=plan.user_id,
            plan_id=plan.id,
            week_start=week_start,
            previous_volume_multiplier=prev,
            new_volume_multiplier=new_vol,
            is_deload=True,
            trigger_reason=trigger_reason,
            explanation_bullets=[
                "This is a deload week to help you recover",
                "Volume reduced by 40%",
                "Focus on form over intensity",
            ],
            metrics_snapshot=_metrics_snapshot(metrics),
            explanation_title="Deload week",
        )
        self.db.add(adj)
        self.db.commit()
        self.db.refresh(adj)
        return adj

    def _create_volume_reduction(
        self,
        plan: TrainingPlan,
        trigger_reason: str,
        week_start: date,
        metrics: Optional[UserBehaviorMetrics],
    ) -> Optional[WeeklyPlanAdjustment]:
        prev = plan.volume_multiplier or 1.0
        new_vol = _clamp_volume(prev * 0.8)
        if round(new_vol, 2) == round(prev, 2):
            return None
        plan.volume_multiplier = new_vol
        adj = WeeklyPlanAdjustment(
            id=uuid4(),
            user_id=plan.user_id,
            plan_id=plan.id,
            week_start=week_start,
            previous_volume_multiplier=prev,
            new_volume_multiplier=new_vol,
            is_deload=False,
            trigger_reason=trigger_reason,
            explanation_bullets=[
                "Volume reduced by 20% to support recovery",
                "Focus on consistency this week",
            ],
            metrics_snapshot=_metrics_snapshot(metrics),
            explanation_title="Volume reduced",
        )
        self.db.add(adj)
        self.db.commit()
        self.db.refresh(adj)
        return adj

    def _create_volume_increase(
        self,
        plan: TrainingPlan,
        trigger_reason: str,
        week_start: date,
        metrics: Optional[UserBehaviorMetrics],
    ) -> Optional[WeeklyPlanAdjustment]:
        prev = plan.volume_multiplier or 1.0
        new_vol = _clamp_volume(min(1.2, prev + 0.1))
        if round(new_vol, 2) == round(prev, 2):
            return None
        plan.volume_multiplier = new_vol
        adj = WeeklyPlanAdjustment(
            id=uuid4(),
            user_id=plan.user_id,
            plan_id=plan.id,
            week_start=week_start,
            previous_volume_multiplier=prev,
            new_volume_multiplier=new_vol,
            is_deload=False,
            trigger_reason=trigger_reason,
            explanation_bullets=[
                "Momentum is strong — slight volume increase",
                "Keep quality over quantity",
            ],
            metrics_snapshot=_metrics_snapshot(metrics),
            explanation_title="Volume increased",
        )
        self.db.add(adj)
        self.db.commit()
        self.db.refresh(adj)
        return adj
