"""
Workout schemas for API responses and requests.
Shared API contract - frontend depends on exact structure.
"""
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID

from app.utils.enums import LifecycleStatus, CompletionStatus, RPE, SetType


class WorkoutSetOut(BaseModel):
    """Response schema for a workout set."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    set_number: int
    reps: Optional[int] = None
    weight: Optional[float] = None
    duration_seconds: Optional[int] = None
    rpe: Optional[RPE] = None  # Enum (not str)
    set_type: SetType  # Enum (not str)
    rest_time_seconds: Optional[int] = None
    created_at: datetime


class WorkoutExerciseOut(BaseModel):
    """Response schema for a workout exercise."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    exercise_id: UUID
    exercise_name: str
    order_index: int
    notes: Optional[str] = None
    sets: List[WorkoutSetOut] = []
    created_at: datetime


class WorkoutOut(BaseModel):
    """Full workout response schema (for detail view)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    lifecycle_status: LifecycleStatus  # Enum (not str)
    completion_status: Optional[CompletionStatus] = None  # Enum (not str)
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    name: Optional[str] = None
    notes: Optional[str] = None
    exercises: List[WorkoutExerciseOut] = []
    created_at: datetime
    updated_at: datetime


class ActiveWorkoutSummary(BaseModel):
    """Schema for active draft workout summary.
    
    Separate from WorkoutSummary to keep history schema strict.
    Drafts don't have completion_status, so we need a different schema.
    
    Contract: start_time must be timezone-aware (TIMESTAMPTZ).
    FastAPI will serialize as ISO datetime with Z or offset.
    Frontend timer depends on accurate timezone-aware timestamps.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    date: date  # Computed using user timezone
    name: Optional[str] = None
    exercise_count: int
    set_count: int
    start_time: datetime  # Timezone-aware (TIMESTAMPTZ) - needed for timer on frontend


class WorkoutSummary(BaseModel):
    """Lightweight workout summary (for history list)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    date: date  # date type (cleaner than str)
    name: Optional[str] = None
    duration_minutes: Optional[int] = None
    exercise_count: int
    set_count: int
    completion_status: CompletionStatus  # Enum (not str)


class AddExerciseToWorkoutIn(BaseModel):
    """Request schema for adding exercise to workout."""
    model_config = ConfigDict(from_attributes=True)
    
    exercise_id: UUID = Field(..., description="Exercise library ID")
    order_index: Optional[int] = Field(None, description="Optional order index (auto-incremented if not provided)")
    notes: Optional[str] = Field(None, max_length=500, description="Optional exercise notes")


class FinishWorkoutIn(BaseModel):
    """Request schema for finishing workout.
    
    Note: Used in later days (Week 1 Day 4+ or Week 3) for finish workout endpoint.
    Defined here to establish shared API contract early.
    """
    model_config = ConfigDict(from_attributes=True)
    
    completion_status: CompletionStatus  # Enum: "completed" or "partial"
    notes: Optional[str] = Field(None, max_length=2000)


class UpdateWorkoutIn(BaseModel):
    """Request schema for updating workout name/notes.
    
    Both fields are optional - can update name only, notes only, or both.
    Uses Pydantic's exclude_unset=True to only send provided fields.
    Empty string "" clears the field (sets to None if DB allows NULL).
    """
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, max_length=200, description="Workout name")
    notes: Optional[str] = Field(None, max_length=2000, description="Workout notes")


class AddSetToExerciseIn(BaseModel):
    """Request schema for adding set to workout exercise."""
    model_config = ConfigDict(from_attributes=True)
    
    set_number: Optional[int] = Field(None, description="Optional set number (auto-incremented if not provided)")
    reps: Optional[int] = Field(None, ge=1, description="Number of reps")
    weight: Optional[float] = Field(None, ge=0, description="Weight in kg")
    duration_seconds: Optional[int] = Field(None, ge=1, description="Duration in seconds (for time-based exercises)")
    set_type: SetType = Field(SetType.WORKING, description="Set type (working, warmup, failure, drop, amrap)")
    rpe: Optional[RPE] = Field(None, description="Rate of perceived exertion (easy, medium, hard)")
    rest_time_seconds: Optional[int] = Field(None, ge=0, description="Rest time in seconds")


class UpdateSetIn(BaseModel):
    """Request schema for updating set (partial update)."""
    model_config = ConfigDict(from_attributes=True)
    
    # Note: set_number is NOT included to prevent ordering issues and duplicates
    # If you need to reorder sets, delete and recreate them instead
    # Option B (if you want to allow set_number editing): include it and enforce uniqueness in update_set()
    reps: Optional[int] = Field(None, ge=1, description="Number of reps")
    weight: Optional[float] = Field(None, ge=0, description="Weight in kg")
    duration_seconds: Optional[int] = Field(None, ge=1, description="Duration in seconds")
    set_type: Optional[SetType] = Field(None, description="Set type")
    rpe: Optional[RPE] = Field(None, description="Rate of perceived exertion")
    rest_time_seconds: Optional[int] = Field(None, ge=0, description="Rest time in seconds")


class ReorderExerciseItem(BaseModel):
    """Single exercise reorder item."""
    workout_exercise_id: UUID = Field(..., description="Workout exercise UUID")
    order_index: int = Field(..., ge=0, description="New order index (0-based)")


class ReorderExercisesIn(BaseModel):
    """Request schema for reordering exercises in workout."""
    items: List[ReorderExerciseItem] = Field(..., min_length=1, description="List of exercises with new order_index")


class PreviousSetPerformance(BaseModel):
    """Previous set performance data."""
    set_number: int
    reps: Optional[int] = None
    weight: Optional[float] = None
    duration_seconds: Optional[int] = None
    set_type: SetType


class LastPerformanceOut(BaseModel):
    """Response schema for last performance of exercise."""
    last_date: date = Field(..., description="Date of last workout with this exercise (YYYY-MM-DD)")
    workout_id: UUID = Field(..., description="Workout UUID")
    sets: List[PreviousSetPerformance] = Field(..., description="List of sets from last workout")


class WorkoutHistoryOut(BaseModel):
    """Response schema for workout history with pagination."""
    items: List[WorkoutSummary] = Field(..., description="List of workout summaries")
    next_cursor: Optional[str] = Field(None, description="Cursor for next page (ISO UTC timestamp with Z + id tie-breaker, format: 'timestamp|uuid'), or null if no more")
