"""Schemas for transformation predictions (Phase 2 Week 6)."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TransformationPredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    computed_at: datetime
    strength_gain_weeks: Optional[int] = None
    visible_change_weeks: Optional[int] = None
    next_milestone: Optional[str] = None
    next_milestone_weeks: Optional[int] = None
    weeks_delta: Optional[int] = None
    delta_reason: Optional[str] = None
    current_consistency_score: Optional[float] = None
    current_workouts_per_week: Optional[float] = None
    primary_goal: Optional[str] = None  # strength, muscle, weight_loss, general
