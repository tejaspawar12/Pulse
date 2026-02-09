"""Refresh token model for secure session management."""
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    token_family_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    replaced_by_id = Column(UUID(as_uuid=True), ForeignKey("refresh_tokens.id", ondelete="CASCADE"), nullable=True)
    used_at = Column(DateTime(timezone=True), nullable=True)

    device_info = Column(String(255), nullable=True)
    ip_hash = Column(String(64), nullable=True)

    __table_args__ = (
        Index('ix_refresh_tokens_user_expires', 'user_id', 'expires_at'),
        Index('ix_refresh_tokens_family', 'token_family_id'),
        Index('ix_refresh_tokens_hash', 'token_hash'),
        Index('ix_refresh_tokens_revoked', 'revoked_at'),
    )
