"""
Coach chat message — one turn in the coach conversation (user or assistant).
Used for multi-turn chat in the Coach tab.
"""
from sqlalchemy import Column, DateTime, String, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base


class CoachChatMessage(Base):
    __tablename__ = "coach_chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
