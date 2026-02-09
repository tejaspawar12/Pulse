"""
Training plan — per-user plan parameters (Phase 2 Week 7).
One plan per user (unique on user_id).
"""
from sqlalchemy import Column, DateTime, Float, Integer, String, Boolean, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base


class TrainingPlan(Base):
    __tablename__ = "training_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    days_per_week = Column(Integer, nullable=True)
    session_duration_target = Column(Integer, nullable=True)  # minutes
    split_type = Column(String(30), nullable=True)  # full_body, upper_lower, push_pull_legs
    volume_multiplier = Column(Float, default=1.0, nullable=False)
    progression_type = Column(String(30), nullable=True)  # linear, wave, autoregulated
    auto_adjust_enabled = Column(Boolean, default=False, nullable=False)
    deload_week_frequency = Column(Integer, default=4, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
