"""
User coach profile — coaching preferences (Phase 2 Week 5).
"""
from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid

from app.models.base import Base


class UserCoachProfile(Base):
    __tablename__ = "user_coach_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    primary_goal = Column(String(50), nullable=True)  # strength, muscle, weight_loss, general
    experience_level = Column(String(20), nullable=True)  # beginner, intermediate, advanced
    target_days_per_week = Column(Integer, nullable=True)
    target_session_minutes = Column(Integer, nullable=True)
    available_equipment = Column(ARRAY(String), nullable=True)
    preferred_workout_time = Column(String(20), nullable=True)  # morning, afternoon, evening

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
