from sqlalchemy import Boolean, Column, Date, DateTime, Float, Integer, String, Time, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    units = Column(String, default="kg", nullable=False)  # kg or lb
    timezone = Column(String, default="Asia/Kolkata", nullable=False)  # Source of truth
    default_rest_timer_seconds = Column(Integer, default=90, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Body / personal (for coach, plan, predictions)
    weight_kg = Column(Float, nullable=True)
    height_cm = Column(Float, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)  # male, female, other, prefer_not_say

    # Entitlement / email verification (Phase 2 Week 1)
    email_verified = Column(Boolean, default=False, nullable=False)
    entitlement = Column(String(20), default="free", nullable=False)  # "free" | "pro"
    pro_trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    trial_used = Column(Boolean, default=False, nullable=False)

    # Notification preferences (Phase 2 Week 2)
    notifications_enabled = Column(Boolean, default=True, nullable=False)
    reminder_time = Column(Time, nullable=True)
