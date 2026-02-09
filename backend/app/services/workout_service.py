"""
Workout service for business logic.
Handles workout modifications, validation, and business rules.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.orm import joinedload, selectinload
from typing import Optional, List, TypedDict, NotRequired
from uuid import UUID
from datetime import datetime, timezone

from app.models.workout import Workout, WorkoutExercise, WorkoutSet
from app.models.exercise import ExerciseLibrary
from app.utils.enums import LifecycleStatus, SetType, RPE, CompletionStatus
from app.schemas.workout import WorkoutOut, WorkoutSetOut, LastPerformanceOut, PreviousSetPerformance
from app.config.settings import settings


class WorkoutUpdatePayload(TypedDict, total=False):
    """Type-safe payload for workout updates."""
    name: NotRequired[str | None]
    notes: NotRequired[str | None]


class WorkoutService:
    def __init__(self, db: Session):
        self.db = db
        # ✅ Load abandonment constant from settings
        self.abandon_after_hours = int(settings.ABANDON_AFTER_HOURS)
    
    def start_workout(self, user_id: UUID) -> WorkoutOut:
        """
        Start a new workout or return existing draft.
        
        Uses unique index to prevent multiple drafts per user.
        If draft exists, returns it. Otherwise creates new.
        Auto-abandons old drafts >= 24h old.
        
        Args:
            user_id: User UUID
        
        Returns:
            WorkoutOut: Draft workout with start_time
        """
        from sqlalchemy.exc import IntegrityError
        
        # Try to get existing draft first
        existing_draft = (
            self.db.query(Workout)
            .filter(
                Workout.user_id == user_id,
                Workout.lifecycle_status == LifecycleStatus.DRAFT.value
            )
            .order_by(Workout.start_time.desc())
            .first()
        )
        
        if existing_draft:
            # ✅ Check if draft is old enough to abandon (>= 24h)
            if self._should_abandon_workout(existing_draft):
                self._abandon_workout(existing_draft)
                # After abandoning, create new draft
            else:
                return self._get_workout_detail(existing_draft.id)
        
        # Create new draft workout
        workout = Workout(
            user_id=user_id,
            lifecycle_status=LifecycleStatus.DRAFT.value
        )
        
        try:
            self.db.add(workout)
            self.db.commit()
            self.db.refresh(workout)
        except IntegrityError:
            # Race condition: another request created draft, re-query
            self.db.rollback()
            existing_draft = (
                self.db.query(Workout)
                .filter(
                    Workout.user_id == user_id,
                    Workout.lifecycle_status == LifecycleStatus.DRAFT.value
                )
                .order_by(Workout.start_time.desc())
                .first()
            )
            if existing_draft:
                # ✅ Check if draft is old enough to abandon (>= 24h)
                if self._should_abandon_workout(existing_draft):
                    self._abandon_workout(existing_draft)
                    # After abandoning, create new draft (continue below)
                else:
                    return self._get_workout_detail(existing_draft.id)
            raise
        
        return self._get_workout_detail(workout.id)
    
    def get_active_workout(self, user_id: UUID) -> Optional[WorkoutOut]:
        """
        Get active draft workout for user.
        Auto-abandons old drafts >= 24h old.
        
        Args:
            user_id: User UUID
        
        Returns:
            WorkoutOut or None: Active workout or None if none
        """
        workout = (
            self.db.query(Workout)
            .filter(
                Workout.user_id == user_id,
                Workout.lifecycle_status == LifecycleStatus.DRAFT.value
            )
            .order_by(Workout.start_time.desc())
            .first()
        )
        
        if not workout:
            return None
        
        # ✅ Check if draft is old enough to abandon (>= 24h)
        if self._should_abandon_workout(workout):
            self._abandon_workout(workout)
            return None  # No active workout after abandonment
        
        return self._get_workout_detail(workout.id)
    
    def get_workout_for_modification(
        self,
        workout_id: UUID,
        user_id: UUID
    ) -> Workout:
        """
        Get workout and validate it can be modified.
        
        Enforces:
        - Workout must exist (404 if not found)
        - Workout must belong to user (403 if not)
        - Workout must be draft (400 if finalized/abandoned)
        
        Args:
            workout_id: Workout UUID
            user_id: Current user UUID
        
        Returns:
            Workout: Validated workout
        
        Raises:
            HTTPException: 404 if not found, 403 if wrong user, 400 if not draft
        """
        from fastapi import HTTPException, status
        
        workout = self.db.query(Workout).filter(Workout.id == workout_id).first()
        
        if not workout:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout not found"
            )
        
        if workout.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this workout"
            )
        
        if workout.lifecycle_status != LifecycleStatus.DRAFT.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify finalized workout"
            )
        
        return workout
    
    def add_exercise_to_workout(
        self,
        workout_id: UUID,
        user_id: UUID,
        exercise_id: UUID,
        order_index: Optional[int] = None,
        notes: Optional[str] = None
    ) -> WorkoutOut:
        """
        Add exercise to workout.
        
        Enforces:
        - Workout must be draft
        - Workout must belong to user
        - Exercise must exist
        
        Args:
            workout_id: Workout UUID
            user_id: Current user UUID
            exercise_id: Exercise library UUID
            order_index: Optional order index (auto-incremented if not provided)
            notes: Optional exercise notes
        
        Returns:
            WorkoutOut: Updated workout with new exercise
        
        Raises:
            HTTPException: 404 if workout/exercise not found, 403 if wrong user, 400 if not draft
        """
        from fastapi import HTTPException, status
        
        # Validate workout can be modified
        workout = self.get_workout_for_modification(workout_id, user_id)
        
        # Verify exercise exists
        exercise = self.db.query(ExerciseLibrary).filter(
            ExerciseLibrary.id == exercise_id
        ).first()
        
        if not exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found"
            )
        
        # Check if exercise already in workout (optional - allow duplicates for now)
        # Could add check here: existing = db.query(WorkoutExercise).filter(...).first()
        
        # Auto-increment order_index if not provided
        # Use 0-based indexing (first exercise = 0, second = 1, etc.)
        if order_index is None:
            max_order = self.db.query(func.max(WorkoutExercise.order_index)).filter(
                WorkoutExercise.workout_id == workout_id
            ).scalar()
            # If no exercises exist, start at 0. Otherwise, increment from max.
            order_index = (max_order + 1) if max_order is not None else 0
        
        # Create workout exercise
        workout_exercise = WorkoutExercise(
            workout_id=workout_id,
            exercise_id=exercise_id,
            order_index=order_index,
            notes=notes
        )
        
        self.db.add(workout_exercise)
        self.db.commit()
        self.db.refresh(workout_exercise)
        
        # Return full workout with exercises
        return self._get_workout_detail(workout_id)
    
    def reorder_exercises(
        self,
        workout_id: UUID,
        user_id: UUID,
        items: List[dict]  # List of {workout_exercise_id: UUID, order_index: int}
    ) -> WorkoutOut:
        """
        Reorder exercises in workout.
        
        Enforces:
        - Workout must be draft
        - Workout must belong to user
        - All exercises must belong to workout
        - All order_index values must be unique (0, 1, 2, ...)
        
        Args:
            workout_id: Workout UUID
            user_id: Current user UUID
            items: List of {workout_exercise_id: UUID, order_index: int}
        
        Returns:
            WorkoutOut: Updated workout with reordered exercises
        
        Raises:
            HTTPException: 404 if workout not found, 403 if wrong user, 400 if not draft or validation fails
        """
        from fastapi import HTTPException, status
        
        # Validate workout can be modified (draft-only, user ownership)
        workout = self.get_workout_for_modification(workout_id, user_id)
        
        # Get all workout exercises for this workout
        workout_exercises = (
            self.db.query(WorkoutExercise)
            .filter(WorkoutExercise.workout_id == workout_id)
            .all()
        )
        
        # Create mapping of workout_exercise_id -> WorkoutExercise
        exercise_map = {we.id: we for we in workout_exercises}
        
        # Validate all exercises belong to workout
        for item in items:
            if item['workout_exercise_id'] not in exercise_map:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Exercise {item['workout_exercise_id']} does not belong to this workout"
                )
        
        # Validate order_index values are unique and sequential (0, 1, 2, ...)
        order_indices = sorted([item['order_index'] for item in items])
        expected_indices = list(range(len(items)))
        if order_indices != expected_indices:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"order_index values must be unique and sequential starting from 0. Got: {order_indices}"
            )
        
        # Validate all exercises in workout are included
        if len(items) != len(workout_exercises):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Must include all exercises in workout. Expected {len(workout_exercises)}, got {len(items)}"
            )
        
        # Update order_index for each exercise
        for item in items:
            exercise = exercise_map[item['workout_exercise_id']]
            exercise.order_index = item['order_index']
        
        self.db.commit()
        self.db.refresh(workout)
        
        # Return full workout with reordered exercises
        return self._get_workout_detail(workout_id)
    
    def add_set_to_exercise(
        self,
        workout_exercise_id: UUID,
        user_id: UUID,
        set_number: Optional[int] = None,
        reps: Optional[int] = None,
        weight: Optional[float] = None,
        duration_seconds: Optional[int] = None,
        set_type: SetType = SetType.WORKING,
        rpe: Optional[RPE] = None,
        rest_time_seconds: Optional[int] = None
    ) -> WorkoutSetOut:
        """
        Add set to workout exercise.
        
        Enforces:
        - Workout must be draft
        - Workout must belong to user
        - Workout exercise must exist
        
        Args:
            workout_exercise_id: Workout exercise UUID
            user_id: Current user UUID
            set_number: Optional set number (auto-incremented if not provided)
            reps: Number of reps
            weight: Weight in kg
            duration_seconds: Duration in seconds (for time-based exercises)
            set_type: Set type (default: WORKING)
            rpe: Rate of perceived exertion
            rest_time_seconds: Rest time in seconds
        
        Returns:
            WorkoutSetOut: Created set
        
        Raises:
            HTTPException: 404 if workout exercise not found, 403 if wrong user, 400 if not draft
        """
        from fastapi import HTTPException, status
        from sqlalchemy import func
        
        # Get workout exercise and validate
        workout_exercise = (
            self.db.query(WorkoutExercise)
            .filter(WorkoutExercise.id == workout_exercise_id)
            .first()
        )
        
        if not workout_exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout exercise not found"
            )
        
        # Validate workout can be modified (draft-only, user ownership)
        self.get_workout_for_modification(workout_exercise.workout_id, user_id)
        
        # Auto-increment set_number if not provided
        # Use 0-based indexing (first set = 0, second = 1, etc.)
        # Note: Race condition possible if two requests hit simultaneously
        # For Day 3, this is acceptable. For production, add:
        # - Database unique constraint: Unique(workout_exercise_id, set_number)
        # - Retry logic on IntegrityError (see production-ready upgrade below)
        if set_number is None:
            max_set_number = self.db.query(func.max(WorkoutSet.set_number)).filter(
                WorkoutSet.workout_exercise_id == workout_exercise_id
            ).scalar()
            # If no sets exist, start at 0. Otherwise, increment from max.
            set_number = (max_set_number + 1) if max_set_number is not None else 0
        
        # Validate at least one of reps/weight/duration is present
        if reps is None and weight is None and duration_seconds is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Set must include at least one of: reps, weight, or duration_seconds"
            )
        
        # Create workout set
        # Note: SQLAlchemy model stores set_type and rpe as strings
        # Pydantic will coerce string values to enum types in WorkoutSetOut
        workout_set = WorkoutSet(
            workout_exercise_id=workout_exercise_id,
            set_number=set_number,
            reps=reps,
            weight=weight,
            duration_seconds=duration_seconds,
            set_type=set_type.value,  # Store as string (matches DB column type)
            rpe=rpe.value if rpe else None,  # Store as string or None
            rest_time_seconds=rest_time_seconds
        )
        
        self.db.add(workout_set)
        self.db.commit()
        self.db.refresh(workout_set)
        
        # Convert to Pydantic schema
        return WorkoutSetOut.model_validate(workout_set)
    
    def update_set(
        self,
        set_id: UUID,
        user_id: UUID,
        patch: "UpdateSetIn"
    ) -> WorkoutSetOut:
        """
        Update set (partial update).
        
        Enforces:
        - Workout must be draft
        - Workout must belong to user
        - Set must exist and belong to workout exercise
        
        Uses Pydantic's model_dump(exclude_unset=True) to only update provided fields.
        This correctly handles None values (explicitly set) vs unset fields.
        
        Args:
            set_id: Set UUID
            user_id: Current user UUID
            patch: UpdateSetIn schema with fields to update
        
        Returns:
            WorkoutSetOut: Updated set
        
        Raises:
            HTTPException: 404 if set not found, 403 if wrong user, 400 if not draft
        """
        from fastapi import HTTPException, status
        from app.schemas.workout import UpdateSetIn
        from sqlalchemy.orm import joinedload
        
        # Get set with workout exercise relationship (eager load to avoid surprises)
        # Always eager load relationships before accessing them
        workout_set = (
            self.db.query(WorkoutSet)
            .options(joinedload(WorkoutSet.workout_exercise))
            .filter(WorkoutSet.id == set_id)
            .first()
        )
        
        if not workout_set:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Set not found"
            )
        
        # Validate workout can be modified (draft-only, user ownership)
        # workout_exercise is guaranteed to be loaded due to joinedload above
        self.get_workout_for_modification(workout_set.workout_exercise.workout_id, user_id)
        
        # Get only fields that were explicitly set in the request
        # exclude_unset=True means only fields provided in request are included
        data = patch.model_dump(exclude_unset=True)
        
        # Option A (recommended for Day 3): Prevent set_number editing entirely
        # If set_number is in data, raise error (shouldn't happen if schema excludes it, but defensive check)
        if "set_number" in data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="set_number cannot be updated. Delete and recreate the set to change order."
            )
        
        # Update fields (only those provided in request)
        for key, value in data.items():
            if key in ("set_type", "rpe") and value is not None:
                # Enums: convert to string value for storage
                setattr(workout_set, key, value.value)
            else:
                # Regular fields: set as-is (including None if explicitly provided)
                setattr(workout_set, key, value)
        
        self.db.commit()
        self.db.refresh(workout_set)
        
        # Convert to Pydantic schema
        return WorkoutSetOut.model_validate(workout_set)
    
    def delete_set(
        self,
        set_id: UUID,
        user_id: UUID
    ) -> None:
        """
        Delete set.
        
        Enforces:
        - Workout must be draft
        - Workout must belong to user
        - Set must exist and belong to workout exercise
        
        Args:
            set_id: Set UUID
            user_id: Current user UUID
        
        Raises:
            HTTPException: 404 if set not found, 403 if wrong user, 400 if not draft
        """
        from fastapi import HTTPException, status
        from sqlalchemy.orm import joinedload
        
        # Get set with workout exercise relationship (eager load to avoid surprises)
        # Always eager load relationships before accessing them
        workout_set = (
            self.db.query(WorkoutSet)
            .options(joinedload(WorkoutSet.workout_exercise))
            .filter(WorkoutSet.id == set_id)
            .first()
        )
        
        if not workout_set:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Set not found"
            )
        
        # Validate workout can be modified (draft-only, user ownership)
        # workout_exercise is guaranteed to be loaded due to joinedload above
        self.get_workout_for_modification(workout_set.workout_exercise.workout_id, user_id)
        
        # Delete set
        self.db.delete(workout_set)
        self.db.commit()
    
    def update_workout(
        self,
        workout_id: UUID,
        user_id: UUID,
        update_data: WorkoutUpdatePayload
    ) -> WorkoutOut:
        """
        Update workout name/notes (draft only).
        
        ⚠️ CRITICAL: Single query with eager loading (no double fetch on success)
        ⚠️ NOTE: May do 2 queries on failure (for detailed error messages: 404 vs 403 vs 400)
        
        Enforces:
        - Workout must be draft (400 if finalized/abandoned)
        - Workout must belong to user (403 if not)
        
        Args:
            workout_id: Workout UUID
            user_id: User UUID
            update_data: WorkoutUpdatePayload with fields to update (from exclude_unset=True)
        
        Returns:
            WorkoutOut: Updated workout with full details
        
        Raises:
            HTTPException: 404 if not found, 403 if wrong user, 400 if not draft
        """
        from fastapi import HTTPException, status
        
        # Step 1: Query workout ONCE with eager loading (CRITICAL: no double fetch on success)
        # ⚠️ FIX: Don't use get_workout_for_modification() - it doesn't eager load
        # Query directly with filters and eager loading
        workout = (
            self.db.query(Workout)
            .options(
                selectinload(Workout.exercises)
                .selectinload(WorkoutExercise.sets),
                selectinload(Workout.exercises)
                .selectinload(WorkoutExercise.exercise)
            )
            .filter(
                Workout.id == workout_id,
                Workout.user_id == user_id,
                Workout.lifecycle_status == LifecycleStatus.DRAFT.value
            )
            .first()
        )
        
        # Step 2: Validate workout exists and is draft
        # ⚠️ NOTE: This may do a second query on failure (for detailed error messages)
        # This is acceptable tradeoff: detailed errors (404/403/400) vs strict "one query"
        # If you want strict "one query", return 404 always (like session endpoint)
        if not workout:
            # Could be: not found, wrong user, or not draft
            # Check if workout exists at all (for better error message)
            exists = (
                self.db.query(Workout)
                .filter(Workout.id == workout_id)
                .first()
            )
            
            if not exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Workout not found"
                )
            elif exists.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to modify this workout"
                )
            else:
                # Exists, owned by user, but not draft
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot modify finalized workout"
                )
        
        # Step 3: Update fields from update_data (only provided fields)
        # ⚠️ FIX: Use exclude_unset=True pattern - only update what's provided
        # ⚠️ CRITICAL: Empty string "" clears to None (DB schema allows NULL)
        # Verified: workouts.name and workouts.notes both have nullable=True
        if "name" in update_data:
            # Empty string clears to None (column allows NULL)
            workout.name = update_data["name"] if update_data["name"] else None
        if "notes" in update_data:
            # Empty string clears to None (column allows NULL)
            workout.notes = update_data["notes"] if update_data["notes"] else None
        
        # Step 4: Commit changes
        self.db.commit()
        
        # Step 5: Return updated workout (relationships already loaded)
        # ⚠️ CRITICAL: No need to call _get_workout_detail() - workout already has exercises/sets loaded
        return WorkoutOut.model_validate(workout)

    def discard_workout(self, workout_id: UUID, user_id: UUID) -> None:
        """
        Discard (abandon) a draft workout. User explicitly cancels without saving.
        Sets lifecycle_status='abandoned'; workout will not appear in history.

        Enforces:
        - Workout must be draft (400 if finalized/abandoned)
        - Workout must belong to user (403 if not)

        Args:
            workout_id: Workout UUID
            user_id: User UUID

        Raises:
            HTTPException: 404 if not found, 403 if wrong user, 400 if not draft
        """
        from fastapi import HTTPException, status

        workout = (
            self.db.query(Workout)
            .filter(
                Workout.id == workout_id,
                Workout.user_id == user_id,
                Workout.lifecycle_status == LifecycleStatus.DRAFT.value,
            )
            .first()
        )
        if not workout:
            exists = self.db.query(Workout).filter(Workout.id == workout_id).first()
            if not exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Workout not found",
                )
            if exists.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to discard this workout",
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot discard finalized workout",
            )
        self._abandon_workout(workout)
    
    def finish_workout(
        self,
        workout_id: UUID,
        user_id: UUID,
        completion_status: CompletionStatus,
        notes: Optional[str] = None
    ) -> WorkoutOut:
        """
        Finish workout (finalize).
        
        Enforces:
        - Workout must be draft (400 if finalized/abandoned)
        - Workout must belong to user (403 if not)
        - Idempotent-safe: If already finalized, returns existing (200)
        - Validation: Cannot finish with 0 sets unless status is "partial"
        
        Args:
            workout_id: Workout UUID
            user_id: User UUID
            completion_status: CompletionStatus enum (completed or partial)
            notes: Optional workout notes
        
        Returns:
            WorkoutOut: Finalized workout with full details
        
        Raises:
            HTTPException: 404 if not found, 403 if wrong user, 400 if validation fails
        """
        from fastapi import HTTPException, status
        from app.models.daily_training_state import DailyTrainingState
        from app.models.user import User
        from sqlalchemy import text, func
        from sqlalchemy.dialects.postgresql import insert
        
        # Step 1: Get workout with eager loading (OPTIMIZATION: avoid double fetch)
        workout = (
            self.db.query(Workout)
            .options(
                selectinload(Workout.exercises)
                .selectinload(WorkoutExercise.sets),
                selectinload(Workout.exercises)
                .selectinload(WorkoutExercise.exercise)
            )
            .filter(Workout.id == workout_id)
            .first()
        )
        
        if not workout:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout not found"
            )
        
        # Step 2: Check ownership
        if workout.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to finish this workout"
            )
        
        # Step 3: Idempotent-safe checks (LOCKED)
        if workout.lifecycle_status == LifecycleStatus.FINALIZED.value:
            # Already finalized - return existing (idempotent)
            # Use already-loaded workout to avoid extra query
            return WorkoutOut.model_validate(workout)
        
        if workout.lifecycle_status == LifecycleStatus.ABANDONED.value:
            # Cannot finish abandoned workout
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot finish abandoned workout"
            )
        
        # Step 4: Validate non-empty workout (LOCKED)
        # Prevent finishing with 0 sets unless status is partial
        total_sets = sum(
            len(ex.sets) if ex.sets else 0
            for ex in workout.exercises
        ) if workout.exercises else 0
        
        if total_sets == 0:
            # No sets logged - only allow if partial status
            if completion_status != CompletionStatus.PARTIAL:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot finish workout with no sets. Use 'partial' status if workout was incomplete."
                )
        
        # Step 5: Set end_time, lifecycle, completion status, and notes
        # ⚠️ CRITICAL: Do everything in one transaction (no mid-way commits)
        # Use flush() to get DB timestamps without committing
        
        # Set end_time using database now() (timezone-aware)
        workout.end_time = func.now()
        
        # Set lifecycle and completion status
        workout.lifecycle_status = LifecycleStatus.FINALIZED.value
        workout.completion_status = completion_status.value
        
        # Update notes if provided
        if notes is not None:
            workout.notes = notes
        
        # Flush to get end_time populated from DB (without committing)
        # This ensures end_time is available for duration calculation
        self.db.flush()
        
        # Step 6: Calculate duration_minutes (in same transaction)
        # Compute duration after flush (end_time is now available)
        if workout.start_time and workout.end_time:
            delta = workout.end_time - workout.start_time
            workout.duration_minutes = int(delta.total_seconds() / 60)
        
        # Step 7: Write to daily_training_state (LOCKED - DB-level upsert)
        # Get user timezone
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_timezone = user.timezone or "Asia/Kolkata"
        
        # Calculate date using Postgres AT TIME ZONE (LOCKED)
        # This ensures correct date regardless of server timezone
        date_query = text(
            "SELECT DATE(start_time AT TIME ZONE :tz) as workout_date "
            "FROM workouts WHERE id = :workout_id"
        )
        result = self.db.execute(
            date_query,
            {"tz": user_timezone, "workout_id": workout_id}
        ).fetchone()
        
        workout_date = result.workout_date if result else None
        
        if workout_date:
            # ⚠️ CRITICAL: Use DB-level upsert (ON CONFLICT) to prevent race conditions
            # Two requests finishing at same time can both try to insert → duplicate row
            # Solution: Use Postgres ON CONFLICT DO UPDATE
            # 
            # ⚠️ FIX: Use index_elements instead of constraint name (safer across migrations)
            # SQLAlchemy UniqueConstraint doesn't automatically name itself unless explicitly named
            # Using index_elements is more reliable
            
            # ⚠️ DECISION: workout_id behavior (LOCKED)
            # Option A: Store last workout of the day (overwrite if exists) - RECOMMENDED
            # We choose Option A: Last workout of the day (overwrite OK)
            # Reason: Most recent workout is more relevant for daily state
            
            stmt = insert(DailyTrainingState).values(
                user_id=user_id,
                date=workout_date,
                worked_out=True,
                workout_id=workout_id
            )
            
            stmt = stmt.on_conflict_do_update(
                index_elements=["user_id", "date"],  # Use index_elements (safer than constraint name)
                set_={
                    'worked_out': True,
                    'workout_id': workout_id,  # Option A: overwrite with latest
                    'updated_at': func.now()
                }
            )
            
            self.db.execute(stmt)
        
        # Step 8: Auto-complete today's commitment when user finishes a workout (Week 5)
        # Only update commitment where status is "yes", not yet completed, same transaction
        from app.models.daily_commitment import DailyCommitment
        from app.utils.timezone import user_today
        
        today = user_today(user_timezone)
        self.db.query(DailyCommitment).filter(
            DailyCommitment.user_id == user_id,
            DailyCommitment.commitment_date == today,
            DailyCommitment.status == "yes",
            DailyCommitment.completed.is_(False),
        ).update(
            {
                "completed": True,
                "completed_at": datetime.now(timezone.utc),
                "workout_id": workout_id,
            },
            synchronize_session=False,
        )
        
        # Step 9: Commit all changes in one transaction
        self.db.commit()
        
        # Step 10: Return workout (handle relationship expiration)
        # ⚠️ CRITICAL: refresh() can expire relationship collections
        # If relationships are expired, WorkoutOut.model_validate() might trigger lazy-loads (N+1)
        # 
        # Relationships loaded in step 1 should remain valid after commit
        # No refresh needed - relationships are still valid
        # If your setup expires relationships on commit, use:
        # return self._get_workout_detail(workout_id)  # Re-query with eager load
        
        # Convert to schema (workout already has exercises/sets loaded from step 1)
        return WorkoutOut.model_validate(workout)
    
    def _should_abandon_workout(self, workout: Workout) -> bool:
        """
        Check if workout should be abandoned (>= 24h old).
        
        ⚠️ CRITICAL: Uses Python datetime.now(timezone.utc) for compatibility with freezegun.
        If using SQL now(), freezegun won't freeze database time → flaky tests.
        
        Args:
            workout: Workout to check
        
        Returns:
            bool: True if workout should be abandoned
        """
        if not workout.start_time:
            return False  # No start time, can't determine age
        
        # ✅ Use Python datetime for age calculation (works with freezegun)
        now_utc = datetime.now(timezone.utc)
        
        # Ensure start_time is timezone-aware for comparison
        start_time_utc = workout.start_time
        if start_time_utc.tzinfo is None:
            # If naive, assume UTC (shouldn't happen with timezone=True column, but safe)
            start_time_utc = start_time_utc.replace(tzinfo=timezone.utc)
        else:
            # Convert to UTC if timezone-aware
            start_time_utc = start_time_utc.astimezone(timezone.utc)
        
        age_hours = (now_utc - start_time_utc).total_seconds() / 3600
        
        return age_hours >= self.abandon_after_hours
    
    def _abandon_workout(self, workout: Workout) -> None:
        """
        Abandon a workout (set lifecycle_status='abandoned', completion_status=None).
        
        Args:
            workout: Workout to abandon
        """
        workout.lifecycle_status = LifecycleStatus.ABANDONED.value
        workout.completion_status = None
        self.db.commit()
        self.db.refresh(workout)
    
    def _get_workout_detail(self, workout_id: UUID) -> WorkoutOut:
        """
        Get full workout detail with exercises and sets.
        
        Eager loads exercises, sets, and exercise library.
        
        Args:
            workout_id: Workout UUID
        
        Returns:
            WorkoutOut: Full workout with exercises and sets
        """
        from fastapi import HTTPException, status
        
        # Use selectinload for better performance with nested relationships
        # This loads exercises and sets in separate queries (more efficient than nested joinedload)
        workout = (
            self.db.query(Workout)
            .options(
                selectinload(Workout.exercises).selectinload(WorkoutExercise.exercise),
                selectinload(Workout.exercises).selectinload(WorkoutExercise.sets)
            )
            .filter(Workout.id == workout_id)
            .first()
        )
        
        if not workout:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout not found"
            )
        
        # Convert to Pydantic schema
        # exercise_name is read from ORM property (WorkoutExercise.exercise_name)
        # See model definition: WorkoutExercise has @property exercise_name
        workout_out = WorkoutOut.model_validate(workout)
        
        return workout_out
    
    def get_last_performance(
        self,
        exercise_id: UUID,
        user_id: UUID
    ) -> Optional["LastPerformanceOut"]:
        """
        Get last logged performance for exercise.
        
        Queries the most recent finalized workout that includes this exercise,
        and returns the sets from that workout.
        
        Args:
            exercise_id: Exercise library UUID
            user_id: Current user UUID
        
        Returns:
            LastPerformanceOut or None if never logged
        """
        from app.schemas.workout import LastPerformanceOut, PreviousSetPerformance
        from app.utils.enums import SetType
        from sqlalchemy import desc
        from datetime import date
        
        # Find most recent finalized workout with this exercise
        workout_exercise = (
            self.db.query(WorkoutExercise)
            .join(Workout)
            .filter(
                WorkoutExercise.exercise_id == exercise_id,
                Workout.user_id == user_id,
                Workout.lifecycle_status == LifecycleStatus.FINALIZED.value
            )
            .order_by(desc(Workout.start_time))
            .first()
        )
        
        if not workout_exercise:
            return None
        
        # Get workout to access start_time
        workout = workout_exercise.workout
        
        # Get all sets for this exercise in this workout
        sets = (
            self.db.query(WorkoutSet)
            .filter(WorkoutSet.workout_exercise_id == workout_exercise.id)
            .order_by(WorkoutSet.set_number)
            .all()
        )
        
        # Convert sets to PreviousSetPerformance
        previous_sets = [
            PreviousSetPerformance(
                set_number=set.set_number,
                reps=set.reps,
                weight=set.weight,
                duration_seconds=set.duration_seconds,
                set_type=SetType(set.set_type)  # Convert string to enum
            )
            for set in sets
        ]
        
        # Calculate date from start_time (using user's timezone if available)
        # For Day 4, use UTC date (can enhance with timezone in Week 3)
        workout_date = workout.start_time.date()
        
        return LastPerformanceOut(
            last_date=workout_date,
            workout_id=workout.id,
            sets=previous_sets
        )
    
    def get_workout_history(
        self,
        user_id: UUID,
        user_timezone: str,
        cursor_time: Optional[datetime] = None,
        cursor_id: Optional[UUID] = None,
        limit: int = 20
    ) -> tuple[List["WorkoutSummary"], Optional[str]]:
        """
        Get workout history with pagination (cursor-based).
        
        ⚠️ CRITICAL: Uses SQL aggregates to avoid N+1 queries
        - Computes date in main query (not per row)
        - Computes exercise_count and set_count using SQL aggregates
        - Single query returns all data needed for WorkoutSummary
        
        ⚠️ CRITICAL: Uses (start_time, id) tie-breaker for stable pagination
        - Prevents duplicates/skips when workouts have same start_time
        - Cursor encodes both timestamp and ID
        
        History includes: finalized workouts with completed/partial
        History excludes: abandoned workouts
        
        Args:
            user_id: User UUID
            user_timezone: User timezone (e.g., "Asia/Kolkata") - passed from endpoint
            cursor_time: Optional cursor timestamp (start_time of last item from previous page, timezone-aware)
            cursor_id: Optional cursor ID (id of last item from previous page) - for tie-breaker
            limit: Maximum number of items (default 20)
        
        Returns:
            Tuple of (workout summaries list, next_cursor as ISO UTC string with ID or None)
        """
        from app.schemas.workout import WorkoutSummary
        from sqlalchemy import select, func as sql_func, or_, and_
        from sqlalchemy.exc import DBAPIError, ProgrammingError
        from datetime import timezone as tz
        
        # Note: func is already imported at module level, sql_func is alias for clarity
        
        # Use default timezone if not provided
        user_timezone = user_timezone or "Asia/Kolkata"
        
        # Build subqueries for exercise and set counts
        exercise_count_subq = (
            select(
                WorkoutExercise.workout_id,
                sql_func.count(WorkoutExercise.id).label('exercise_count')
            )
            .group_by(WorkoutExercise.workout_id)
            .subquery()
        )
        
        # Use outerjoin so exercises with 0 sets count as 0 sets (future-proof)
        set_count_subq = (
            select(
                WorkoutExercise.workout_id,
                sql_func.count(WorkoutSet.id).label('set_count')
            )
            .outerjoin(WorkoutSet, WorkoutExercise.id == WorkoutSet.workout_exercise_id)
            .group_by(WorkoutExercise.workout_id)
            .subquery()
        )
        
        # Build query with date and counts computed in SQL
        safe_timezone = user_timezone
        
        query_with_counts = (
            self.db.query(
                Workout.id,
                Workout.name,
                Workout.duration_minutes,
                Workout.completion_status,
                Workout.start_time,
                func.date(func.timezone(safe_timezone, Workout.start_time)).label('workout_date'),
                sql_func.coalesce(exercise_count_subq.c.exercise_count, 0).label('exercise_count'),
                sql_func.coalesce(set_count_subq.c.set_count, 0).label('set_count')
            )
            .outerjoin(exercise_count_subq, Workout.id == exercise_count_subq.c.workout_id)
            .outerjoin(set_count_subq, Workout.id == set_count_subq.c.workout_id)
            .filter(
                Workout.user_id == user_id,
                Workout.lifecycle_status == LifecycleStatus.FINALIZED.value,
                Workout.completion_status.in_([
                    CompletionStatus.COMPLETED.value,
                    CompletionStatus.PARTIAL.value
                ]),
                Workout.start_time.isnot(None)
            )
        )
        
        # Apply cursor with tie-breaker (start_time, id)
        if cursor_time:
            if cursor_id:
                query_with_counts = query_with_counts.filter(
                    or_(
                        Workout.start_time < cursor_time,
                        and_(
                            Workout.start_time == cursor_time,
                            Workout.id < cursor_id
                        )
                    )
                )
            else:
                # Fallback: timestamp only (accepts small risk of ties)
                query_with_counts = query_with_counts.filter(Workout.start_time < cursor_time)
        
        # Order by (start_time, id) DESC for stable pagination
        query_with_counts = query_with_counts.order_by(
            Workout.start_time.desc(),
            Workout.id.desc()
        )
        
        # Execute query with timezone error handling
        try:
            results = query_with_counts.limit(limit + 1).all()
        except (DBAPIError, ProgrammingError):
            # Timezone invalid -> fallback safely and rebuild query
            safe_timezone = "Asia/Kolkata"
            query_with_counts = (
                self.db.query(
                    Workout.id,
                    Workout.name,
                    Workout.duration_minutes,
                    Workout.completion_status,
                    Workout.start_time,
                    func.date(func.timezone(safe_timezone, Workout.start_time)).label('workout_date'),
                    sql_func.coalesce(exercise_count_subq.c.exercise_count, 0).label('exercise_count'),
                    sql_func.coalesce(set_count_subq.c.set_count, 0).label('set_count')
                )
                .outerjoin(exercise_count_subq, Workout.id == exercise_count_subq.c.workout_id)
                .outerjoin(set_count_subq, Workout.id == set_count_subq.c.workout_id)
                .filter(
                    Workout.user_id == user_id,
                    Workout.lifecycle_status == LifecycleStatus.FINALIZED.value,
                    Workout.completion_status.in_([
                        CompletionStatus.COMPLETED.value,
                        CompletionStatus.PARTIAL.value
                    ]),
                    Workout.start_time.isnot(None)
                )
            )
            # Re-apply cursor filter if needed
            if cursor_time:
                if cursor_id:
                    query_with_counts = query_with_counts.filter(
                        or_(
                            Workout.start_time < cursor_time,
                            and_(
                                Workout.start_time == cursor_time,
                                Workout.id < cursor_id
                            )
                        )
                    )
                else:
                    query_with_counts = query_with_counts.filter(Workout.start_time < cursor_time)
            # Re-apply ordering
            query_with_counts = query_with_counts.order_by(
                Workout.start_time.desc(),
                Workout.id.desc()
            )
            # Retry query
            results = query_with_counts.limit(limit + 1).all()
        
        # Check if there are more items
        has_more = len(results) > limit
        if has_more:
            results = results[:limit]
        
        # Convert to WorkoutSummary
        summaries = []
        for row in results:
            summary = WorkoutSummary(
                id=row.id,
                date=row.workout_date,
                name=row.name,
                duration_minutes=row.duration_minutes,
                exercise_count=row.exercise_count or 0,
                set_count=row.set_count or 0,
                completion_status=CompletionStatus(row.completion_status)
            )
            summaries.append(summary)
        
        # Calculate next_cursor (start_time + id of last item, or None)
        next_cursor = None
        if has_more and results:
            last_row = results[-1]
            last_start_time = last_row.start_time
            last_id = last_row.id
            
            # Ensure timezone-aware
            if last_start_time.tzinfo is None:
                last_start_time = last_start_time.replace(tzinfo=tz.utc)
            else:
                last_start_time = last_start_time.astimezone(tz.utc)
            
            # Format as ISO with Z
            timestamp_str = last_start_time.isoformat().replace("+00:00", "Z")
            
            # Encode both timestamp and ID in cursor (format: "timestamp|id")
            next_cursor = f"{timestamp_str}|{str(last_id)}"
        
        return summaries, next_cursor
    
    def get_workout_detail(
        self,
        workout_id: UUID,
        user_id: UUID
    ) -> WorkoutOut:
        """
        Get workout detail by ID.
        
        Enforces:
        - Workout must exist (404 if not found)
        - Workout must belong to user (403 if not)
        
        Uses _get_workout_detail() which has eager loading.
        
        ⚠️ NOTE: Current approach does two queries (one for ownership check, one for eager loading).
        This is acceptable if we want to return 403 for wrong user (requires knowing workout exists).
        Alternative: Single query with eager loading + ownership filter, return 404 for all failures.
        Current approach is fine for clarity of error messages.
        
        Args:
            workout_id: Workout UUID
            user_id: User UUID (for ownership check)
        
        Returns:
            WorkoutOut: Full workout with exercises and sets
        
        Raises:
            HTTPException: 404 if not found, 403 if wrong user
        """
        from fastapi import HTTPException, status
        
        # Check workout exists and ownership
        workout = (
            self.db.query(Workout)
            .filter(Workout.id == workout_id)
            .first()
        )
        
        if not workout:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout not found"
            )
        
        if workout.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this workout"
            )
        
        # Return full workout with eager loading
        return self._get_workout_detail(workout_id)
