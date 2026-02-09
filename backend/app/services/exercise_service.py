"""
Exercise service for business logic.
Handles exercise search, filtering, and recent exercises.
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, text, bindparam, select
from typing import List, Optional
from uuid import UUID

from app.models.exercise import ExerciseLibrary
from app.models.workout import Workout, WorkoutExercise
from app.utils.enums import LifecycleStatus, CompletionStatus
from app.schemas.exercise import ExerciseOut


class ExerciseService:
    def __init__(self, db: Session):
        self.db = db
    
    def search_exercises(
        self,
        query: Optional[str] = None,
        muscle_group: Optional[str] = None,
        equipment: Optional[str] = None,
        limit: int = 50
    ) -> List[ExerciseOut]:
        """
        Search exercises with trigram fuzzy matching.
        
        Search Logic (LOCKED):
        - If query length < 2: return empty list (trigram on 1 char is noisy)
        - If query length >= 2: search in name, normalized_name, and aliases
        - Use trigram (%) for fuzzy matching on name
        - Use ILIKE for normalized_name
        - Use exact match (LOWER(:q) = ANY(aliases)) for aliases
        
        Args:
            query: Search query string (minimum 2 characters)
            muscle_group: Filter by primary muscle group
            equipment: Filter by equipment type
            limit: Maximum number of results (default 50)
        
        Returns:
            List[ExerciseOut]: List of matching exercises
        """
        # Start with base query
        base_query = self.db.query(ExerciseLibrary)
        
        # Build search conditions
        conditions = []
        
        if query and len(query) >= 2:
            # Normalize query (lowercase, trimmed)
            normalized_query = query.lower().strip()
            
            # Build search conditions (LOCKED query plan)
            # 1. Trigram fuzzy match on name using % operator (handles typos)
            # 2. ILIKE on name (partial match)
            # 3. ILIKE on normalized_name (case-insensitive)
            # 4. Exact match on aliases array using LOWER(:q) = ANY(aliases)
            # Note: Use text() with bindparam for trigram, func.any_() for array operations
            # normalized_query is already sanitized (lowercased, trimmed) and validated by FastAPI
            search_conditions = or_(
                text("exercise_library.name % :q").bindparams(bindparam("q", normalized_query)),  # Trigram similarity operator (%)
                ExerciseLibrary.name.ilike(f'%{normalized_query}%'),
                ExerciseLibrary.normalized_name.ilike(f'%{normalized_query}%'),
                func.lower(normalized_query) == func.any_(ExerciseLibrary.aliases)  # Array match
            )
            
            conditions.append(search_conditions)
        elif query and len(query) < 2:
            # Query too short - return empty list
            return []
        
        # Add filters
        if muscle_group:
            conditions.append(ExerciseLibrary.primary_muscle_group == muscle_group.lower())
        
        if equipment:
            conditions.append(ExerciseLibrary.equipment == equipment.lower())
        
        # Apply all conditions
        if conditions:
            base_query = base_query.filter(and_(*conditions))
        
        # Order by relevance (if search query provided)
        if query and len(query) >= 2:
            normalized_query = query.lower().strip()
            # Order by trigram similarity (highest first)
            # Use similarity() function for ordering
            base_query = base_query.order_by(
                func.similarity(ExerciseLibrary.name, normalized_query).desc()
            )
        else:
            # Order by name alphabetically
            base_query = base_query.order_by(ExerciseLibrary.name)
        
        # Limit results
        exercises = base_query.limit(limit).all()
        
        # Convert to Pydantic schemas
        return [ExerciseOut.model_validate(ex) for ex in exercises]
    
    def get_recent_exercises(self, user_id: UUID, limit: int = 10) -> List[ExerciseOut]:
        """
        Get exercises used in last 10 workouts for a user.
        
        Args:
            user_id: User UUID
            limit: Maximum number of exercises to return (default 10)
        
        Returns:
            List[ExerciseOut]: List of recent exercises, ordered by most recent use
        """
        # Query workouts that are finalized (completed or partial)
        # Use subquery to get max start_time per exercise, then join and order by recency
        # This avoids DISTINCT ON ordering issues
        
        # Subquery: get max start_time for each exercise from finalized workouts
        max_start_time_subq = (
            select(
                WorkoutExercise.exercise_id,
                func.max(Workout.start_time).label('max_start_time')
            )
            .join(Workout, WorkoutExercise.workout_id == Workout.id)
            .where(
                Workout.user_id == user_id,
                Workout.lifecycle_status == LifecycleStatus.FINALIZED.value,
                Workout.completion_status.in_([
                    CompletionStatus.COMPLETED.value,
                    CompletionStatus.PARTIAL.value
                ])
            )
            .group_by(WorkoutExercise.exercise_id)
            .subquery()
        )
        
        # Main query: join exercises with max start_time, order by recency
        recent_exercises = (
            self.db.query(ExerciseLibrary)
            .join(max_start_time_subq, ExerciseLibrary.id == max_start_time_subq.c.exercise_id)
            .order_by(max_start_time_subq.c.max_start_time.desc())
            .limit(limit)
            .all()
        )
        
        # Convert to Pydantic schemas
        return [ExerciseOut.model_validate(ex) for ex in recent_exercises]
