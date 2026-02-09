"""Schemas for coach profile (goal and preferences)."""
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

PRIMARY_GOAL_VALUES = frozenset({"strength", "muscle", "weight_loss", "general"})


class CoachProfileOut(BaseModel):
    """Coach profile as returned by GET /coach/profile."""
    primary_goal: Optional[str] = None  # strength, muscle, weight_loss, general
    experience_level: Optional[str] = None
    target_days_per_week: Optional[int] = None
    target_session_minutes: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class CoachProfileUpdate(BaseModel):
    """Body for PATCH /coach/profile. All fields optional."""
    primary_goal: Optional[str] = None  # strength, muscle, weight_loss, general

    @field_validator("primary_goal")
    @classmethod
    def validate_primary_goal(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        normalized = v.strip().lower()
        if normalized not in PRIMARY_GOAL_VALUES:
            raise ValueError(
                "primary_goal must be one of: strength, muscle, weight_loss, general"
            )
        return normalized
