"""
Weekly training report — per-user, per-week snapshot (Phase 2 Week 6).
Unique on (user_id, week_start).
"""
from sqlalchemy import Column, Date, DateTime, Float, Integer, String, Text, ForeignKey, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.models.base import Base


class WeeklyTrainingReport(Base):
    __tablename__ = "weekly_training_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    week_start = Column(Date, nullable=False)  # Monday of the week
    week_end = Column(Date, nullable=False)   # Sunday of the week

    workouts_count = Column(Integer, nullable=True)  # Number of finalized workouts
    total_volume_kg = Column(Float, nullable=True)
    volume_delta_pct = Column(Float, nullable=True)   # % change vs previous week
    prs_hit = Column(Integer, nullable=True)         # Optional, can be 0 for MVP
    avg_session_duration = Column(Float, nullable=True)  # Minutes

    primary_training_mistake_key = Column(String(50), nullable=True)
    primary_training_mistake_label = Column(String(255), nullable=True)
    weekly_focus_key = Column(String(50), nullable=True)
    weekly_focus_label = Column(String(255), nullable=True)
    positive_signal_key = Column(String(50), nullable=True)   # Learning feedback
    positive_signal_label = Column(String(255), nullable=True)
    positive_signal_reason = Column(String(255), nullable=True)
    reasons = Column(JSONB, nullable=True)  # From metrics

    narrative = Column(Text, nullable=True)          # LLM-generated summary
    narrative_source = Column(String(20), nullable=True)  # "llm" | "fallback" | null
    status = Column(String(20), nullable=False)      # "generated" | "insufficient_data"
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    narrative_generated_at = Column(DateTime(timezone=True), nullable=True)  # Optional for MVP

    __table_args__ = (
        UniqueConstraint("user_id", "week_start", name="uq_weekly_report_user_week"),
    )
