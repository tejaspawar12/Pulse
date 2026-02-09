"""
User behavior metrics — daily snapshot per user (Phase 2 Week 5).
"""
from sqlalchemy import Column, DateTime, Float, Integer, String, ForeignKey, func, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.types import Date
import uuid

from app.models.base import Base


class UserBehaviorMetrics(Base):
    __tablename__ = "user_behavior_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    computed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    metrics_date = Column(Date, nullable=False)  # User's local date for unique constraint

    consistency_score = Column(Float, nullable=True)  # 0-100
    dropout_risk = Column(String(20), nullable=True)  # low, medium, high
    burnout_risk = Column(String(20), nullable=True)
    momentum_trend = Column(String(20), nullable=True)  # rising, stable, falling
    adherence_type = Column(String(30), nullable=True)  # consistent, weekend_warrior, sporadic

    workouts_last_7_days = Column(Integer, nullable=True)
    workouts_last_14_days = Column(Integer, nullable=True)
    avg_session_duration_minutes = Column(Float, nullable=True)
    total_volume_last_7_days = Column(Float, nullable=True)
    volume_delta_vs_prev_week = Column(Float, nullable=True)
    max_gap_days = Column(Integer, nullable=True)
    common_skip_day = Column(String(10), nullable=True)  # monday, tuesday, etc.

    primary_training_mistake_key = Column(String(50), nullable=True)
    primary_training_mistake_label = Column(String(255), nullable=True)
    weekly_focus_key = Column(String(50), nullable=True)
    weekly_focus_label = Column(String(255), nullable=True)

    reasons = Column(JSONB, nullable=True)  # [{"reason_key": "...", "reason_label": "..."}]

    __table_args__ = (
        UniqueConstraint("user_id", "metrics_date", name="uq_user_behavior_metrics_user_date"),
        Index("ix_behavior_metrics_user_computed", "user_id", "computed_at"),
    )
