"""
Plan API: current plan, create, preferences, adjustment history (Phase 2 Week 7).
Auto-adjust available to all users.
"""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.api.deps import get_db, get_current_user_auto
from app.models.user import User
from app.schemas.plan import (
    PlanOut,
    AdjustmentOut,
    PlanCurrentResponse,
    PlanPreferencesUpdate,
)
from app.services.plan_service import PlanService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/plan", tags=["plan"])

PLAN_TABLES_MESSAGE = (
    "Plan feature is not available. Ensure database migrations are run: alembic upgrade head"
)


@router.get("/current", response_model=PlanCurrentResponse)
def get_plan_current(
    current_user: User = Depends(get_current_user_auto),
    db=Depends(get_db),
):
    """Current plan + this week's adjustment. 404 if no plan. Ensures this week's adjustment is computed if auto_adjust is on."""
    try:
        svc = PlanService(db)
        plan = svc.get_current_plan(current_user.id)
        if not plan:
            raise HTTPException(status_code=404, detail="No plan found")
        this_week = svc.get_this_week_adjustment(current_user.id)
        if plan.auto_adjust_enabled and this_week is None:
            week_start = svc.get_this_week_start(current_user.id)
            if week_start:
                svc.compute_weekly_adjustment(current_user.id, week_start)
                db.commit()
                plan = svc.get_current_plan(current_user.id)
                this_week = svc.get_this_week_adjustment(current_user.id)
        return PlanCurrentResponse(
            plan=PlanOut.model_validate(plan),
            this_week_adjustment=AdjustmentOut.model_validate(this_week) if this_week else None,
        )
    except HTTPException:
        raise
    except (OperationalError, ProgrammingError) as e:
        logger.exception("Plan tables missing or DB error in get_plan_current")
        raise HTTPException(status_code=503, detail=PLAN_TABLES_MESSAGE) from e
    except Exception as e:
        logger.exception("Unexpected error in get_plan_current")
        raise HTTPException(status_code=500, detail="Failed to load plan") from e


@router.post("/create", response_model=PlanOut)
def create_plan(
    current_user: User = Depends(get_current_user_auto),
    db=Depends(get_db),
):
    """Create initial plan (idempotent: return existing if present)."""
    try:
        svc = PlanService(db)
        return svc.create_plan(current_user.id)
    except (OperationalError, ProgrammingError) as e:
        logger.exception("Plan tables missing or DB error in create_plan")
        raise HTTPException(status_code=503, detail=PLAN_TABLES_MESSAGE) from e
    except Exception as e:
        logger.exception("Unexpected error in create_plan")
        raise HTTPException(status_code=500, detail="Failed to create plan") from e


@router.patch("/preferences", response_model=PlanOut)
def update_plan_preferences(
    body: PlanPreferencesUpdate,
    current_user: User = Depends(get_current_user_auto),
    db=Depends(get_db),
):
    """Update plan preferences. Auto-adjust available to all users."""
    try:
        svc = PlanService(db)
        kwargs = body.model_dump(exclude_unset=True)
        return svc.update_preferences(
            current_user.id,
            current_user,
            **kwargs,
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except (OperationalError, ProgrammingError) as e:
        logger.exception("Plan tables missing or DB error in update_plan_preferences")
        raise HTTPException(status_code=503, detail=PLAN_TABLES_MESSAGE) from e
    except Exception as e:
        logger.exception("Unexpected error in update_plan_preferences")
        raise HTTPException(status_code=500, detail="Failed to update plan") from e


@router.get("/history", response_model=List[AdjustmentOut])
def get_plan_history(
    current_user: User = Depends(get_current_user_auto),
    db=Depends(get_db),
    limit: int = Query(12, ge=1, le=50, description="Max adjustments to return"),
):
    """Adjustment history (week_start desc). Include metrics_snapshot in each item."""
    try:
        svc = PlanService(db)
        adjustments = svc.get_adjustment_history(current_user.id, limit=limit)
        return [AdjustmentOut.model_validate(a) for a in adjustments]
    except (OperationalError, ProgrammingError) as e:
        logger.exception("Plan tables missing or DB error in get_plan_history")
        raise HTTPException(status_code=503, detail=PLAN_TABLES_MESSAGE) from e
    except Exception as e:
        logger.exception("Unexpected error in get_plan_history")
        raise HTTPException(status_code=500, detail="Failed to load plan history") from e
