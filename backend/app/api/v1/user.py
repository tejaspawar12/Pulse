"""
User API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db, get_current_user_dev, get_current_user_auto
from app.models.user import User
from app.schemas.user import UserStatusOut, UserOut, UpdateUserIn
from app.schemas.workout import LastPerformanceOut
from app.services.user_status_service import UserStatusService
from app.services.workout_service import WorkoutService
from app.services.user_service import UserService

router = APIRouter()


@router.get("/users/me", response_model=UserOut)
def get_current_user_profile(
    current_user: User = Depends(get_current_user_auto),  # Supports both JWT and dev auth
    db: Session = Depends(get_db)
):
    """
    Get current user profile.
    
    Returns:
        UserOut: User profile with id, email, units, timezone, default_rest_timer_seconds
    """
    return current_user


@router.patch("/users/me", response_model=UserOut)
def update_user_settings(
    data: UpdateUserIn,
    current_user: User = Depends(get_current_user_auto),  # Supports both JWT and dev auth
    db: Session = Depends(get_db)
):
    """
    Update current user settings.
    
    ⚠️ CRITICAL: Verify router prefix in main.py ensures final path is /api/v1/users/me
    
    Args:
        data: Update data (units, timezone, default_rest_timer_seconds)
        current_user: Current user (from JWT or dev auth)
        db: Database session
    
    Returns:
        UserOut: Updated user data
    
    Raises:
        400: Validation error (invalid timezone)
        401: Not authenticated
        404: User not found (shouldn't happen, but handled)
    """
    service = UserService(db)
    updated_user = service.update_user_settings(current_user.id, data)
    
    return UserOut.model_validate(updated_user)


@router.get("/me/status", response_model=UserStatusOut)
def get_user_status(
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db)
):
    """
    Get user status: active workout, today's status, last 30 days.
    
    Returns:
        UserStatusOut: User status with:
        - active_workout: ActiveWorkoutSummary or None (draft workout summary)
        - today_worked_out: boolean (whether user worked out today in their timezone)
        - last_30_days: List of DailyStatus (date, worked_out) ordered oldest→newest
    """
    try:
        service = UserStatusService(db)
        result = service.get_user_status(current_user.id)
        return result
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/users/me/exercises/{exercise_id}/last-performance", response_model=LastPerformanceOut)
def get_last_performance(
    exercise_id: UUID,
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db)
):
    """
    Get last logged performance for exercise.
    
    Returns the most recent finalized workout that includes this exercise,
    with all sets from that workout.
    
    Args:
        exercise_id: Exercise library UUID
        current_user: Current user (from dependency)
        db: Database session
    
    Returns:
        LastPerformanceOut: Last performance data
    
    Raises:
        404: Exercise never logged or exercise not found
    """
    service = WorkoutService(db)
    last_performance = service.get_last_performance(
        exercise_id=exercise_id,
        user_id=current_user.id
    )
    
    if not last_performance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No previous performance found for this exercise"
        )
    
    return last_performance
