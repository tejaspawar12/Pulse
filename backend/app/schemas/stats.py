"""Stats response schemas for summary, streak, and volume over time."""
from datetime import date
from pydantic import BaseModel, ConfigDict


class StatsSummaryResponse(BaseModel):
    """Summary stats for a period."""
    model_config = ConfigDict(from_attributes=True)

    period_days: int
    total_workouts: int
    total_volume_kg: float
    total_sets: int
    prs_hit: int
    avg_workout_duration_minutes: float | None
    most_trained_muscle: str | None


class StreakResponse(BaseModel):
    """Current and longest streak."""
    model_config = ConfigDict(from_attributes=True)

    current_streak_days: int
    longest_streak_days: int
    last_workout_date: date | None


class VolumeDataPoint(BaseModel):
    """One bucket (day or week) of volume data."""
    period_start: date
    period_end: date
    total_volume_kg: float
    workout_count: int


class VolumeResponse(BaseModel):
    """Volume over time (grouped by day or week)."""
    data: list[VolumeDataPoint]
    period_days: int


class MetricsSummaryResponse(BaseModel):
    """
    Phase 3: Portfolio metrics for Insights.
    GET /api/v1/metrics/summary?days=7|30 — deterministic only (no LLM).
    """
    model_config = ConfigDict(from_attributes=True)

    total_volume_kg: float
    workouts_count: int
    workouts_per_week: float
    volume_by_muscle_group: dict[str, float]
    pr_count: int
    imbalance_hint: str | None
    streak_days: int
    period_days: int
