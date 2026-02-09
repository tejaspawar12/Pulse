"""
Transformation prediction — per-user timeline (Phase 2 Week 6).
One row per computation (history); no unique constraint.
"""
from sqlalchemy import Column, DateTime, Float, Integer, String, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base


class TransformationPrediction(Base):
    __tablename__ = "transformation_predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    computed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    strength_gain_weeks = Column(Integer, nullable=True)   # "Noticeable strength" window
    visible_change_weeks = Column(Integer, nullable=True)  # "Visible body change" window
    next_milestone = Column(String(100), nullable=True)   # e.g. "First strength gains"
    next_milestone_weeks = Column(Integer, nullable=True)
    weeks_delta = Column(Integer, nullable=True)          # Vs previous prediction (+ = farther, − = closer)
    delta_reason = Column(String(255), nullable=True)
    current_consistency_score = Column(Float, nullable=True)
    current_workouts_per_week = Column(Float, nullable=True)
    primary_goal = Column(String(50), nullable=True)  # strength, muscle, weight_loss, general — snapshot for this prediction
