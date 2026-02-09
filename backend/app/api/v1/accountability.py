"""
Accountability API: today's commitment, commit, respond (Phase 2 Week 5 Day 4).
"""
from datetime import date, time
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user_auto
from app.models.user import User
from app.models.daily_commitment import DailyCommitment
from app.models.accountability_event import AccountabilityEvent
from app.utils.timezone import user_today

router = APIRouter(prefix="/accountability", tags=["accountability"])


def _time_to_str(t: Optional[time]) -> Optional[str]:
    if t is None:
        return None
    return t.strftime("%H:%M")


def _str_to_time(s: Optional[str]) -> Optional[time]:
    if not s or not isinstance(s, str):
        return None
    s = s.strip()
    if not s:
        return None
    try:
        parts = s.split(":")
        if len(parts) >= 2:
            h, m = int(parts[0]), int(parts[1])
            if 0 <= h <= 23 and 0 <= m <= 59:
                return time(hour=h, minute=m)
    except (ValueError, IndexError):
        pass
    return None


def _date_from_str(s: Optional[str]) -> Optional[date]:
    if not s or not isinstance(s, str):
        return None
    try:
        return date.fromisoformat(s.strip())
    except ValueError:
        return None


class CommitBody(BaseModel):
    status: str = Field(..., pattern="^(yes|no|rescheduled)$")
    expected_time: Optional[str] = Field(None, description="HH:MM when status=yes")
    expected_duration_minutes: Optional[int] = Field(None, ge=1, le=300)
    rescheduled_to_date: Optional[str] = Field(None, description="YYYY-MM-DD when status=rescheduled")
    rescheduled_to_time: Optional[str] = Field(None, description="HH:MM when status=rescheduled")


class RespondBody(BaseModel):
    response_type: Optional[str] = None


def _commitment_to_response(c: DailyCommitment) -> dict[str, Any]:
    return {
        "commitment_date": str(c.commitment_date),
        "status": c.status,
        "expected_time": _time_to_str(c.expected_time),
        "expected_duration_minutes": c.expected_duration_minutes,
        "rescheduled_to_date": str(c.rescheduled_to_date) if c.rescheduled_to_date else None,
        "rescheduled_to_time": _time_to_str(c.rescheduled_to_time) if c.rescheduled_to_time else None,
        "completed": c.completed,
        "completed_at": c.completed_at.isoformat() if c.completed_at else None,
    }


@router.get("/today")
def get_commitment_today(
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Today's commitment state. Use user timezone for today."""
    tz = (current_user.timezone or "Asia/Kolkata").strip() or "Asia/Kolkata"
    today = user_today(tz)
    c = (
        db.query(DailyCommitment)
        .filter(
            DailyCommitment.user_id == current_user.id,
            DailyCommitment.commitment_date == today,
        )
        .first()
    )
    if not c:
        return {
            "commitment_date": str(today),
            "status": None,
            "expected_time": None,
            "expected_duration_minutes": None,
            "rescheduled_to_date": None,
            "rescheduled_to_time": None,
            "completed": False,
            "completed_at": None,
        }
    return _commitment_to_response(c)


@router.post("/commit")
def commit_today(
    body: CommitBody,
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Create or update today's commitment. Returns updated commitment state."""
    tz = (current_user.timezone or "Asia/Kolkata").strip() or "Asia/Kolkata"
    today = user_today(tz)
    c = (
        db.query(DailyCommitment)
        .filter(
            DailyCommitment.user_id == current_user.id,
            DailyCommitment.commitment_date == today,
        )
        .first()
    )
    is_new = c is None
    if c is None:
        c = DailyCommitment(
            user_id=current_user.id,
            commitment_date=today,
            status=body.status,
            expected_time=_str_to_time(body.expected_time) if body.status == "yes" else None,
            expected_duration_minutes=body.expected_duration_minutes if body.status in ("yes", "rescheduled") else None,
            rescheduled_to_date=_date_from_str(body.rescheduled_to_date) if body.status == "rescheduled" else None,
            rescheduled_to_time=_str_to_time(body.rescheduled_to_time) if body.status == "rescheduled" else None,
        )
        db.add(c)
    else:
        c.status = body.status
        if body.status == "yes":
            c.expected_time = _str_to_time(body.expected_time)
            c.expected_duration_minutes = body.expected_duration_minutes
            c.rescheduled_to_date = None
            c.rescheduled_to_time = None
        elif body.status == "rescheduled":
            c.rescheduled_to_date = _date_from_str(body.rescheduled_to_date)
            c.rescheduled_to_time = _str_to_time(body.rescheduled_to_time)
            c.expected_time = None
            c.expected_duration_minutes = body.expected_duration_minutes
        else:
            c.expected_time = None
            c.expected_duration_minutes = None
            c.rescheduled_to_date = None
            c.rescheduled_to_time = None
    db.flush()
    event = AccountabilityEvent(
        user_id=current_user.id,
        commitment_id=c.id,
        event_type="commitment_created" if is_new else "commitment_updated",
        event_data={"status": body.status},
    )
    db.add(event)
    db.commit()
    db.refresh(c)
    return _commitment_to_response(c)


@router.post("/respond", status_code=204)
def respond_to_followup(
    body: RespondBody,
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
) -> None:
    """Record a follow-up response; creates AccountabilityEvent. Returns 204."""
    event = AccountabilityEvent(
        user_id=current_user.id,
        commitment_id=None,
        event_type="user_reply_to_follow_up",
        event_data={"response_type": body.response_type} if body.response_type else {},
    )
    db.add(event)
    db.commit()
