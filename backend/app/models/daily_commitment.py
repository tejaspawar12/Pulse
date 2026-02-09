"""
Daily commitment — user's commitment for a given day (Phase 2 Week 5).
status: "yes" | "no" | "rescheduled"
"""
from sqlalchemy import Column, DateTime, Integer, String, Boolean, ForeignKey, Time, func, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import Date
import uuid

from app.models.base import Base


class DailyCommitment(Base):
    __tablename__ = "daily_commitments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    commitment_date = Column(Date, nullable=False)  # User's local date

    # status: "yes" | "no" | "rescheduled" (API contract; no boolean committed)
    status = Column(String(20), nullable=True)  # yes, no, rescheduled
    expected_time = Column(Time, nullable=True)  # when status == "yes"
    expected_duration_minutes = Column(Integer, nullable=True)

    rescheduled_to_date = Column(Date, nullable=True)  # when status == "rescheduled"
    rescheduled_to_time = Column(Time, nullable=True)  # when status == "rescheduled"

    completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    workout_id = Column(UUID(as_uuid=True), ForeignKey("workouts.id", ondelete="SET NULL"), nullable=True)

    follow_up_sent = Column(Boolean, default=False, nullable=False)
    escalation_level = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "commitment_date", name="uq_user_commitment_date"),
        Index("ix_commitments_user_date", "user_id", "commitment_date"),
    )
