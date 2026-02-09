"""
Weekly plan adjustment — history of plan changes per week (Phase 2 Week 7).
Unique on (plan_id, week_start). Index (user_id, week_start desc) for history.
"""
from sqlalchemy import Column, Date, DateTime, Float, Integer, String, Boolean, ForeignKey, func, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.models.base import Base


class WeeklyPlanAdjustment(Base):
    __tablename__ = "weekly_plan_adjustments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("training_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    week_start = Column(Date, nullable=False)

    previous_days_per_week = Column(Integer, nullable=True)
    new_days_per_week = Column(Integer, nullable=True)
    previous_volume_multiplier = Column(Float, nullable=True)
    new_volume_multiplier = Column(Float, nullable=True)
    is_deload = Column(Boolean, default=False, nullable=False)
    trigger_reason = Column(String(50), nullable=True)  # burnout, slipping, momentum_up, plateau
    explanation_bullets = Column(JSONB, nullable=True)  # ["Volume reduced by 20%", ...]
    metrics_snapshot = Column(JSONB, nullable=True)  # {consistency_score, burnout_risk, momentum_trend}
    explanation_title = Column(String(80), nullable=True)  # "Deload week", "Volume reduced", "Volume increased"
    applied_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("plan_id", "week_start", name="uq_weekly_plan_adj_plan_week"),
        Index("idx_weekly_adj_user_weekstart", "user_id", "week_start", postgresql_ops={"week_start": "DESC"}),
    )
