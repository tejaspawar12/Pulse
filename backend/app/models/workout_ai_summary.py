"""
Workout AI summary — cached per-workout LLM summary (AI Summaries & Trends).
One row per workout; summary generated on first request and reused.
"""
from sqlalchemy import Column, DateTime, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base


class WorkoutAISummary(Base):
    __tablename__ = "workout_ai_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workout_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workouts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    summary_text = Column(Text, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
