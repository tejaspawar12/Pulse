"""Schemas for weekly training reports (Phase 2 Week 6)."""
from datetime import date, datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class WeeklyReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    week_start: date
    week_end: date
    workouts_count: Optional[int] = None
    total_volume_kg: Optional[float] = None
    volume_delta_pct: Optional[float] = None
    prs_hit: Optional[int] = None
    avg_session_duration: Optional[float] = None
    primary_training_mistake_key: Optional[str] = None
    primary_training_mistake_label: Optional[str] = None
    weekly_focus_key: Optional[str] = None
    weekly_focus_label: Optional[str] = None
    positive_signal_key: Optional[str] = None
    positive_signal_label: Optional[str] = None
    positive_signal_reason: Optional[str] = None
    reasons: Optional[List[dict]] = None
    narrative: Optional[str] = None
    narrative_source: Optional[str] = None
    status: str
    generated_at: datetime
