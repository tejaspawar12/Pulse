"""
Exercise API endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db, get_current_user_auto
from app.models.user import User
from app.schemas.exercise import ExerciseListOut
from app.services.exercise_service import ExerciseService

router = APIRouter()


@router.get("/exercises", response_model=ExerciseListOut)
def search_exercises(
    q: Optional[str] = Query(None, description="Search query (minimum 2 characters)"),
    muscle_group: Optional[str] = Query(None, description="Filter by muscle group"),
    equipment: Optional[str] = Query(None, description="Filter by equipment"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db)
):
    """
    Search exercises with fuzzy matching.
    
    Search uses trigram similarity for fuzzy matching (handles typos).
    Minimum query length: 2 characters.
    
    Returns:
        ExerciseListOut: List of matching exercises
    """
    service = ExerciseService(db)
    exercises = service.search_exercises(
        query=q,
        muscle_group=muscle_group,
        equipment=equipment,
        limit=limit
    )
    
    return ExerciseListOut(exercises=exercises)


@router.get("/exercises/recent", response_model=ExerciseListOut)
def get_recent_exercises(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of exercises"),
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db)
):
    """
    Get exercises used in last workouts for current user.
    
    Returns exercises from finalized workouts (completed or partial),
    ordered by most recent use.
    
    Returns:
        ExerciseListOut: List of recent exercises
    """
    service = ExerciseService(db)
    exercises = service.get_recent_exercises(
        user_id=current_user.id,
        limit=limit
    )
    
    return ExerciseListOut(exercises=exercises)
