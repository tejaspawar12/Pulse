"""
User schemas for API responses.
"""
from typing import List, Optional
from enum import Enum
from datetime import date, datetime, time as dt_time
from pydantic import BaseModel, ConfigDict, Field, field_validator
from uuid import UUID

from app.schemas.workout import ActiveWorkoutSummary


class Units(str, Enum):
    """Weight units enum."""
    kg = "kg"
    lb = "lb"


class DailyStatus(BaseModel):
    """Daily workout status."""
    model_config = ConfigDict(from_attributes=True)
    
    date: date
    worked_out: bool  # Must be proper bool, not string "true"/"false"


class UserStatusOut(BaseModel):
    """Response schema for GET /me/status."""
    model_config = ConfigDict(from_attributes=True)
    
    active_workout: Optional[ActiveWorkoutSummary] = None
    today_worked_out: bool  # Must be proper bool, not string "true"/"false"
    last_30_days: List[DailyStatus]  # Ordered: oldest → newest (LOCKED)


class UpdateUserIn(BaseModel):
    """Request schema for updating user settings."""
    model_config = ConfigDict(from_attributes=True)
    
    # ✅ Use Enum instead of string+regex (cleaner, type-safe)
    units: Optional[Units] = Field(None, description="Weight units (kg or lb)")
    timezone: Optional[str] = Field(None, description="IANA timezone string (e.g., 'America/New_York')")
    # ✅ Basic constraint in schema (ge=0)
    default_rest_timer_seconds: Optional[int] = Field(None, ge=0, description="Default rest timer in seconds")
    # Body / personal (for coach, plan, predictions)
    weight_kg: Optional[float] = Field(None, ge=0, le=500, description="Body weight in kg")
    height_cm: Optional[float] = Field(None, ge=0, le=300, description="Height in cm")
    date_of_birth: Optional[date] = Field(None, description="Date of birth (YYYY-MM-DD)")
    gender: Optional[str] = Field(None, description="male, female, other, prefer_not_say")

    @field_validator("gender")
    @classmethod
    def gender_allowed(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        allowed = {"male", "female", "other", "prefer_not_say"}
        if v.lower() not in allowed:
            raise ValueError("gender must be one of: male, female, other, prefer_not_say")
        return v.lower()


class UserOut(BaseModel):
    """User profile response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    email: str
    units: str  # "kg" or "lb"
    timezone: str
    default_rest_timer_seconds: int
    created_at: datetime
    updated_at: datetime
    # Body / personal
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    # Phase 2 Week 2 — notification preferences
    notifications_enabled: bool = True
    reminder_time: Optional[str] = None  # "HH:MM" or null

    @field_validator("reminder_time", mode="before")
    @classmethod
    def reminder_time_to_str(cls, v: Optional[dt_time]) -> Optional[str]:
        if v is None:
            return None
        if hasattr(v, "strftime"):
            return v.strftime("%H:%M")
        return v
