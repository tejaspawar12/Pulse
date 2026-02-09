"""
Phase 3 — Portfolio metrics for Insights (deterministic layer).
GET /api/v1/metrics/summary?days=7|30 — aggregates stats + volume_by_muscle_group + imbalance_hint.
"""
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user_auto
from app.models.user import User
from app.schemas.stats import MetricsSummaryResponse
from app.services.stats_service import StatsService

router = APIRouter()


@router.get("/metrics/summary", response_model=MetricsSummaryResponse)
def get_metrics_summary(
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
    days: Literal[7, 30] = Query(7, description="Period: 7 or 30 days"),
):
    """
    Phase 3: Single metrics payload for Insights screen.
    Deterministic only (no LLM). Period in user timezone.
    """
    service = StatsService(db)
    return service.get_metrics_summary(
        current_user.id, current_user.timezone or "UTC", days
    )
