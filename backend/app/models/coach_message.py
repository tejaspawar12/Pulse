"""
Coach message — cached daily coach message per user (Phase 2 Week 5).
Source is stored as a column for fast cache/query; payload holds only message content.
"""
from sqlalchemy import Boolean, Column, DateTime, String, ForeignKey, func, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.types import Date
import uuid

from app.models.base import Base


class CoachMessage(Base):
    __tablename__ = "coach_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    message_date = Column(Date, nullable=False)  # User's local date

    source = Column(String(20), nullable=False)  # "ai" | "free_tier" | "unavailable"
    generated_at = Column(DateTime(timezone=True), nullable=True)  # UTC; only when source == "ai"
    model_id = Column(String(128), nullable=True)  # e.g. anthropic.claude-3-haiku-...
    ai_lite_used = Column(Boolean, default=False, nullable=False)  # True if fallback model used

    payload = Column(JSONB, nullable=False)  # {coach_message, quick_replies, one_action_step} only

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "message_date", name="uq_coach_message_user_date"),
        Index("ix_coach_messages_user_date", "user_id", "message_date"),
    )
