"""
Accountability event — log of nudges/escalations (Phase 2 Week 5).
"""
from sqlalchemy import Column, DateTime, String, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.models.base import Base


class AccountabilityEvent(Base):
    __tablename__ = "accountability_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    commitment_id = Column(UUID(as_uuid=True), ForeignKey("daily_commitments.id", ondelete="SET NULL"), nullable=True)

    event_type = Column(String(30), nullable=False)  # prompt, follow_up, escalation, completion
    event_data = Column(JSONB, nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
