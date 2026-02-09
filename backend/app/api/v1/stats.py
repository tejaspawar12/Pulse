"""
Stats API: summary, streak, and volume over time for the current user.
"""
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user_auto
from app.models.user import User
from app.schemas.stats import (
    StatsSummaryResponse,
    StreakResponse,
    VolumeResponse,
)
from app.services.stats_service import StatsService

router = APIRouter()


@router.get("/users/me/stats/summary", response_model=StatsSummaryResponse)
def get_stats_summary(
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365, description="Period length in days"),
):
    """
    Summary stats for the period [today - (days-1), today] in user timezone.
    Only finalized workouts (completed/partial). Volume = sum of (weight * reps) for working sets.
    """
    service = StatsService(db)
    return service.get_summary(current_user.id, current_user.timezone, days)


@router.get("/users/me/stats/streak", response_model=StreakResponse)
def get_stats_streak(
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
):
    """Current streak (from today backwards), longest streak, and last workout date (user timezone)."""
    service = StatsService(db)
    return service.get_streak(current_user.id, current_user.timezone)


@router.get("/users/me/stats/volume", response_model=VolumeResponse)
def get_stats_volume(
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365, description="Period length in days"),
    group_by: Literal["day", "week"] = Query("week", description="Bucket by day or week (Monday–Sunday)"),
):
    """
    Volume over time: buckets by day or week. Returns continuous buckets;
    missing days/weeks have workout_count=0, total_volume_kg=0.
    """
    service = StatsService(db)
    return service.get_volume_over_time(
        current_user.id, current_user.timezone, days, group_by
    )
