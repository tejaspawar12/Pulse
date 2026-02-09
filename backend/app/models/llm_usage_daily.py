"""
LLM usage daily — token/call counts per user per day (Phase 2 Week 5).
"""
from sqlalchemy import Column, DateTime, Integer, ForeignKey, func, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import Date
import uuid

from app.models.base import Base


class LLMUsageDaily(Base):
    __tablename__ = "llm_usage_daily"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    usage_date = Column(Date, nullable=False)

    input_tokens = Column(Integer, default=0, nullable=False)
    output_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)

    coach_calls = Column(Integer, default=0, nullable=False)
    report_calls = Column(Integer, default=0, nullable=False)
    plan_calls = Column(Integer, default=0, nullable=False)
    summary_calls = Column(Integer, default=0, nullable=False)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "usage_date", name="uq_llm_usage_user_date"),
        Index("ix_llm_usage_user_date", "user_id", "usage_date"),
    )
