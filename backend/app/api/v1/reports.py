"""
Reports API: weekly training report latest and history (Phase 2 Week 6).
Available to all authenticated users. Full report including narrative for everyone.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api.deps import get_db, get_current_user_auto
from app.models.user import User
from app.models.weekly_training_report import WeeklyTrainingReport
from app.schemas.report import WeeklyReportOut

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/weekly/latest")
def get_weekly_report_latest(
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
):
    """
    Latest weekly report for current user. 404 if none.
    Available to all authenticated users; includes narrative when present.
    """
    report = (
        db.query(WeeklyTrainingReport)
        .filter(WeeklyTrainingReport.user_id == current_user.id)
        .order_by(desc(WeeklyTrainingReport.week_start))
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="No weekly report found")
    return WeeklyReportOut.model_validate(report).model_dump()


@router.get("/weekly/history")
def get_weekly_report_history(
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
    limit: int = Query(12, ge=1, le=50, description="Max reports to return"),
):
    """Paginated history (week_start desc). Available to all users."""
    reports = (
        db.query(WeeklyTrainingReport)
        .filter(WeeklyTrainingReport.user_id == current_user.id)
        .order_by(desc(WeeklyTrainingReport.week_start))
        .limit(limit)
        .all()
    )
    return [WeeklyReportOut.model_validate(r).model_dump() for r in reports]
