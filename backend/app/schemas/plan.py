"""Schemas for training plan and weekly adjustments (Phase 2 Week 7)."""
from datetime import date, datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    days_per_week: Optional[int] = None
    session_duration_target: Optional[int] = None
    split_type: Optional[str] = None
    volume_multiplier: float = 1.0
    progression_type: Optional[str] = None
    auto_adjust_enabled: bool = False
    deload_week_frequency: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class AdjustmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    plan_id: UUID
    user_id: UUID
    week_start: date
    previous_days_per_week: Optional[int] = None
    new_days_per_week: Optional[int] = None
    previous_volume_multiplier: Optional[float] = None
    new_volume_multiplier: Optional[float] = None
    is_deload: bool = False
    trigger_reason: Optional[str] = None
    explanation_bullets: Optional[List[str]] = None
    metrics_snapshot: Optional[dict[str, Any]] = None
    explanation_title: Optional[str] = None
    applied_at: datetime


class PlanCurrentResponse(BaseModel):
    plan: PlanOut
    this_week_adjustment: Optional[AdjustmentOut] = None


class PlanPreferencesUpdate(BaseModel):
    days_per_week: Optional[int] = None
    session_duration_target: Optional[int] = None
    split_type: Optional[str] = None
    progression_type: Optional[str] = None
    deload_week_frequency: Optional[int] = None
    auto_adjust_enabled: Optional[bool] = None
