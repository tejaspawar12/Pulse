"""
Workout API endpoints.
"""
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db, get_current_user_auto
from app.models.user import User
from app.models.workout import WorkoutExercise
from app.models.workout_ai_summary import WorkoutAISummary
from app.schemas.workout import (
    WorkoutOut, 
    AddExerciseToWorkoutIn, 
    AddSetToExerciseIn, 
    UpdateSetIn, 
    WorkoutSetOut,
    ReorderExercisesIn,
    FinishWorkoutIn,
    UpdateWorkoutIn,
    WorkoutHistoryOut
)
from app.services.workout_service import WorkoutService
from app.services.llm_service import llm_service
from app.utils.timezone import user_today

router = APIRouter()


@router.post("/workouts/start", response_model=WorkoutOut)
def start_workout(
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db)
):
    """
    Start a new workout or return existing draft.
    
    Returns:
        WorkoutOut: Draft workout with start_time
    """
    service = WorkoutService(db)
    return service.start_workout(current_user.id)


@router.get("/workouts/active", response_model=Optional[WorkoutOut])
def get_active_workout(
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db)
):
    """
    Get active draft workout.
    
    Returns:
        WorkoutOut or None: Active workout or None if none (200 status with null body)
        Simpler for frontend than 204 No Content
    """
    service = WorkoutService(db)
    workout = service.get_active_workout(current_user.id)
    
    if not workout:
        return None  # Returns 200 with null body (simpler for frontend)
    
    return workout


@router.post("/workouts/{workout_id}/exercises", response_model=WorkoutOut)
def add_exercise_to_workout(
    workout_id: UUID,
    request: AddExerciseToWorkoutIn,
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db)
):
    """
    Add exercise to workout.
    
    Enforces:
    - Workout must be draft (400 if finalized)
    - Workout must belong to user (403 if not)
    - Exercise must exist (404 if not found)
    
    Args:
        workout_id: Workout UUID
        request: AddExerciseToWorkoutIn (exercise_id, optional order_index, optional notes)
        current_user: Current user (from dependency)
        db: Database session
    
    Returns:
        WorkoutOut: Updated workout with new exercise
    
    Raises:
        404: Workout or exercise not found
        403: Not authorized (wrong user)
        400: Cannot modify finalized workout
    """
    service = WorkoutService(db)
    workout = service.add_exercise_to_workout(
        workout_id=workout_id,
        user_id=current_user.id,
        exercise_id=request.exercise_id,
        order_index=request.order_index,
        notes=request.notes
    )
    
    return workout


@router.post("/workout-exercises/{workout_exercise_id}/sets", response_model=WorkoutSetOut)
def add_set_to_exercise(
    workout_exercise_id: UUID,
    request: AddSetToExerciseIn,
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db)
):
    """
    Add set to workout exercise.
    
    Enforces:
    - Workout must be draft (400 if finalized)
    - Workout must belong to user (403 if not)
    - Workout exercise must exist (404 if not found)
    
    Args:
        workout_exercise_id: Workout exercise UUID
        request: AddSetToExerciseIn (set fields)
        current_user: Current user (from dependency)
        db: Database session
    
    Returns:
        WorkoutSetOut: Created set
    
    Raises:
        404: Workout exercise not found
        403: Not authorized (wrong user)
        400: Cannot modify finalized workout
    """
    service = WorkoutService(db)
    workout_set = service.add_set_to_exercise(
        workout_exercise_id=workout_exercise_id,
        user_id=current_user.id,
        set_number=request.set_number,
        reps=request.reps,
        weight=request.weight,
        duration_seconds=request.duration_seconds,
        set_type=request.set_type,
        rpe=request.rpe,
        rest_time_seconds=request.rest_time_seconds
    )
    
    return workout_set


@router.patch("/sets/{set_id}", response_model=WorkoutSetOut)
def update_set(
    set_id: UUID,
    request: UpdateSetIn,
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db)
):
    """
    Update set (partial update).
    
    Enforces:
    - Workout must be draft (400 if finalized)
    - Workout must belong to user (403 if not)
    - Set must exist (404 if not found)
    - Set belongs to workout (validated via workout_exercise relationship)
    
    Args:
        set_id: Set UUID
        request: UpdateSetIn (partial set fields)
        current_user: Current user (from dependency)
        db: Database session
    
    Returns:
        WorkoutSetOut: Updated set
    
    Raises:
        404: Set not found
        403: Not authorized (wrong user)
        400: Cannot modify finalized workout
    """
    service = WorkoutService(db)
    workout_set = service.update_set(
        set_id=set_id,
        user_id=current_user.id,
        patch=request
    )
    
    return workout_set


@router.delete("/sets/{set_id}", status_code=204)
def delete_set(
    set_id: UUID,
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db)
):
    """
    Delete set.
    
    Enforces:
    - Workout must be draft (400 if finalized)
    - Workout must belong to user (403 if not)
    - Set must exist (404 if not found)
    
    Args:
        set_id: Set UUID
        current_user: Current user (from dependency)
        db: Database session
    
    Returns:
        204 No Content on success
    
    Raises:
        404: Set not found
        403: Not authorized (wrong user)
        400: Cannot modify finalized workout
    """
    from fastapi import status
    
    service = WorkoutService(db)
    service.delete_set(
        set_id=set_id,
        user_id=current_user.id
    )
    
    return None  # 204 No Content


@router.post("/workouts/{workout_id}/finish", response_model=WorkoutOut)
def finish_workout(
    workout_id: UUID,
    request: FinishWorkoutIn,
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db)
):
    """
    Finish workout (finalize).
    
    Enforces:
    - Workout must be draft (400 if finalized/abandoned - handled by service)
    - Workout must belong to user (403 if not)
    - Idempotent-safe: If already finalized, returns existing (200)
    - Validation: Cannot finish with 0 sets unless status is "partial"
    
    Args:
        workout_id: Workout UUID
        request: FinishWorkoutIn (completion_status, optional notes)
        current_user: Current user (from dependency)
        db: Database session
    
    Returns:
        WorkoutOut: Finalized workout with full details
    
    Raises:
        404: Workout not found
        403: Not authorized (wrong user)
        400: Cannot finish abandoned workout or validation fails
    """
    service = WorkoutService(db)
    workout = service.finish_workout(
        workout_id=workout_id,
        user_id=current_user.id,
        completion_status=request.completion_status,
        notes=request.notes
    )
    return workout
    
    # ⚠️ NOTE: Idempotency behavior
    # If workout is already finalized, service returns existing workout (200 OK)
    # This is correct - we don't allow changing completion_status or notes once finalized
    # Client retries with different values will get the original finalized workout
    # This is intentional and prevents accidental modifications


@router.post("/workouts/{workout_id}/discard", status_code=204)
def discard_workout(
    workout_id: UUID,
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
):
    """
    Discard (cancel) the current draft workout. Workout is abandoned and will not appear in history.
    User returns to "Start Workout" state.

    Enforces:
    - Workout must be draft (400 if finalized/abandoned)
    - Workout must belong to user (403 if not)
    """
    service = WorkoutService(db)
    service.discard_workout(workout_id=workout_id, user_id=current_user.id)
    return None


@router.patch("/workouts/{workout_id}", response_model=WorkoutOut)
def update_workout(
    workout_id: UUID,
    request: UpdateWorkoutIn,
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db)
):
    """
    Update workout name/notes (draft only).
    
    Enforces:
    - Workout must be draft (400 if finalized/abandoned)
    - Workout must belong to user (403 if not)
    
    ⚠️ Uses exclude_unset=True to only update provided fields.
    Allows clearing notes by sending empty string "".
    
    Args:
        workout_id: Workout UUID
        request: UpdateWorkoutIn (optional name, notes)
        current_user: Current user (from dependency)
        db: Database session
    
    Returns:
        WorkoutOut: Updated workout with full details
    
    Raises:
        404: Workout not found
        403: Not authorized (wrong user)
        400: Cannot modify finalized workout
    """
    service = WorkoutService(db)
    
    # ⚠️ CRITICAL: Use exclude_unset=True to get only provided fields
    # This allows partial updates and clearing fields (empty string → None)
    update_data = request.model_dump(exclude_unset=True)
    
    workout = service.update_workout(
        workout_id=workout_id,
        user_id=current_user.id,
        update_data=update_data
    )
    
    return workout


@router.get("/workouts/{workout_id}/session", response_model=WorkoutOut)
def get_workout_session(
    workout_id: UUID,
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db)
):
    """
    Get workout session by ID (for restoring after app kill).
    
    Returns full draft workout with exercises + sets.
    Similar to /workouts/active, but allows fetching by specific workout ID.
    
    ⚠️ LOCKED: Only returns draft workouts (404 if finalized/abandoned)
    ⚠️ CRITICAL: Returns 404 for wrong user (not 403) to prevent leaking workout existence
    
    Args:
        workout_id: Workout UUID
        current_user: Current user (from dependency)
        db: Database session
    
    Returns:
        WorkoutOut: Full workout with exercises and sets
    
    Raises:
        404: Workout not found, not draft, or wrong user (all return 404 for security)
    """
    from fastapi import HTTPException, status
    from app.utils.enums import LifecycleStatus
    from app.models.workout import Workout, WorkoutExercise
    from sqlalchemy.orm import selectinload
    from app.schemas.workout import WorkoutOut
    
    # ⚠️ CRITICAL: Query with all filters at once (id + user + draft)
    # Returns 404 for: not found OR not owned OR not draft
    # This prevents leaking that workout exists (security)
    workout = (
        db.query(Workout)
        .options(
            selectinload(Workout.exercises)
            .selectinload(WorkoutExercise.sets),
            selectinload(Workout.exercises)
            .selectinload(WorkoutExercise.exercise)
        )
        .filter(
            Workout.id == workout_id,
            Workout.user_id == current_user.id,
            Workout.lifecycle_status == LifecycleStatus.DRAFT.value
        )
        .first()
    )
    
    if not workout:
        # Could be: not found, wrong user, or not draft
        # Return 404 for all cases (security: don't leak existence)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found or not draft"
        )
    
    # Return full workout (already eager-loaded)
    return WorkoutOut.model_validate(workout)


@router.get("/workouts", response_model=WorkoutHistoryOut)
def get_workout_history(
    cursor: Optional[str] = Query(None, description="Cursor for pagination (ISO UTC timestamp with Z + id tie-breaker, format: 'timestamp|uuid')"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of items (1-100)"),
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db)
):
    """
    Get workout history with pagination.
    
    History includes: finalized workouts with completed/partial
    History excludes: abandoned workouts
    
    Args:
        cursor: Optional cursor (ISO UTC timestamp string with ID, e.g., "2026-01-25T10:30:00Z|uuid")
        limit: Maximum number of items (default 20, max 100)
        current_user: Current user (from dependency)
        db: Database session
    
    Returns:
        WorkoutHistoryOut: History list with pagination cursor
    
    Raises:
        400: Invalid cursor format
    """
    from fastapi import HTTPException, status
    from datetime import datetime, timezone
    from uuid import UUID
    
    # Pass timezone from current_user (avoid extra DB query)
    user_timezone = current_user.timezone or "Asia/Kolkata"
    
    # Parse cursor to extract both timestamp and ID
    # FastAPI automatically URL-decodes query params, so cursor is already decoded
    cursor_time = None
    cursor_id = None
    if cursor:
        # Cursor format: "timestamp|id" (e.g., "2026-01-25T10:30:00Z|uuid")
        if '|' in cursor:
            cursor_parts = cursor.split('|', 1)
            cursor_time_str = cursor_parts[0]
            try:
                cursor_id = UUID(cursor_parts[1])
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid cursor format. Expected 'timestamp|id' (e.g., '2026-01-25T10:30:00Z|uuid') or legacy 'timestamp'."
                )
        else:
            # Legacy format: timestamp only (for backward compatibility)
            cursor_time_str = cursor
        
        try:
            # Handle both Z and +00:00 formats for robustness
            # Only replace Z suffix (not global replace) to handle timestamps like "2026-01-25T10:30:00.123Z"
            cursor_str = cursor_time_str.replace('Z', '+00:00') if cursor_time_str.endswith('Z') else cursor_time_str
            cursor_time = datetime.fromisoformat(cursor_str)
            # Ensure timezone-aware (assume UTC if naive)
            if cursor_time.tzinfo is None:
                cursor_time = cursor_time.replace(tzinfo=timezone.utc)
            else:
                # Convert to UTC (in case it's in different timezone)
                cursor_time = cursor_time.astimezone(timezone.utc)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cursor format. Expected 'timestamp|id' (e.g., '2026-01-25T10:30:00Z|uuid') or legacy 'timestamp'."
            )
    
    service = WorkoutService(db)
    summaries, next_cursor = service.get_workout_history(
        user_id=current_user.id,
        user_timezone=user_timezone,
        cursor_time=cursor_time,
        cursor_id=cursor_id,
        limit=limit
    )
    
    return WorkoutHistoryOut(
        items=summaries,
        next_cursor=next_cursor
    )


@router.get("/workouts/{workout_id}", response_model=WorkoutOut)
def get_workout_detail(
    workout_id: UUID,
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db)
):
    """
    Get workout detail by ID.
    
    Returns full workout with exercises and sets.
    Works for both draft and finalized workouts (read-only).
    
    Args:
        workout_id: Workout UUID
        current_user: Current user (from dependency)
        db: Database session
    
    Returns:
        WorkoutOut: Full workout with exercises and sets
    
    Raises:
        404: Workout not found
        403: Not authorized (wrong user)
    """
    service = WorkoutService(db)
    workout = service.get_workout_detail(
        workout_id=workout_id,
        user_id=current_user.id
    )
    
    return workout


def _workout_to_summary_payload(workout: WorkoutOut) -> dict[str, Any]:
    """Build a compact payload for LLM from WorkoutOut."""
    exercises_payload = []
    for ex in workout.exercises or []:
        sets_payload = [
            {
                "weight": s.weight,
                "reps": s.reps,
                "set_type": getattr(s.set_type, "value", str(s.set_type)) if s.set_type else None,
            }
            for s in ex.sets or []
        ]
        exercises_payload.append({"name": ex.exercise_name or "Exercise", "sets": sets_payload})
    return {
        "date": workout.start_time.date().isoformat() if workout.start_time else None,
        "duration_minutes": workout.duration_minutes,
        "name": workout.name,
        "exercises": exercises_payload,
    }


@router.get("/workouts/{workout_id}/ai-summary")
def get_workout_ai_summary(
    workout_id: UUID,
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """
    Get AI-generated summary for a workout (AI Summaries & Trends).
    Returns cached summary if available; otherwise generates via LLM and caches.
    """
    service = WorkoutService(db)
    workout = service.get_workout_detail(workout_id=workout_id, user_id=current_user.id)

    cached = (
        db.query(WorkoutAISummary)
        .filter(WorkoutAISummary.workout_id == workout_id)
        .first()
    )
    if cached:
        return {"summary": cached.summary_text or ""}

    if not llm_service.bedrock_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI summary is temporarily unavailable. Try again later.",
        )

    payload = _workout_to_summary_payload(workout)
    tz = (current_user.timezone or "Asia/Kolkata").strip() or "Asia/Kolkata"
    usage_date = user_today(tz)
    summary_text, _, _ = llm_service.generate_workout_summary(
        user_id=current_user.id,
        workout_payload=payload,
        usage_date=usage_date,
        db=db,
    )
    if not summary_text:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not generate summary. Try again later.",
        )
    db.add(
        WorkoutAISummary(
            workout_id=workout_id,
            summary_text=summary_text,
        )
    )
    db.commit()
    return {"summary": summary_text}


@router.patch("/workouts/{workout_id}/exercises/reorder", response_model=WorkoutOut)
def reorder_exercises(
    workout_id: UUID,
    request: ReorderExercisesIn,
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db)
):
    """
    Reorder exercises in workout.
    
    Enforces:
    - Workout must be draft (400 if finalized)
    - Workout must belong to user (403 if not)
    - All exercises must belong to workout (400 if not)
    - All order_index values must be unique and sequential (0, 1, 2, ...)
    
    Args:
        workout_id: Workout UUID
        request: ReorderExercisesIn (list of exercises with new order_index)
        current_user: Current user (from dependency)
        db: Database session
    
    Returns:
        WorkoutOut: Updated workout with reordered exercises
    
    Raises:
        404: Workout not found
        403: Not authorized (wrong user)
        400: Cannot modify finalized workout or validation fails
    """
    service = WorkoutService(db)
    
    # Convert Pydantic items to dict format for service method
    items = [
        {
            'workout_exercise_id': item.workout_exercise_id,
            'order_index': item.order_index
        }
        for item in request.items
    ]
    
    workout = service.reorder_exercises(
        workout_id=workout_id,
        user_id=current_user.id,
        items=items
    )
    
    return workout
