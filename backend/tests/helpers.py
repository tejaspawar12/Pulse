"""
Shared test helper functions.
"""
from contextlib import contextmanager
from sqlalchemy import event
from sqlalchemy.engine import Engine
from app.models.workout import Workout
from app.utils.enums import LifecycleStatus, CompletionStatus
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from uuid import UUID

def finalize_workout(db: Session, workout_id: UUID):
    """
    Helper to finalize workout in tests (sets all required fields).
    
    ⚠️ LOCKED: This function is ONLY in helpers.py, NOT in conftest.py.
    This avoids import confusion and keeps tests clean.
    
    This ensures all required fields are set correctly:
    - lifecycle_status = FINALIZED
    - completion_status = COMPLETED
    - end_time = now()
    - duration_minutes = calculated
    """
    workout = db.query(Workout).filter(Workout.id == workout_id).first()
    if workout:
        workout.lifecycle_status = LifecycleStatus.FINALIZED.value
        workout.completion_status = CompletionStatus.COMPLETED.value
        workout.end_time = datetime.now(timezone.utc)
        # Calculate duration_minutes if needed
        if workout.start_time and workout.end_time:
            delta = workout.end_time - workout.start_time
            workout.duration_minutes = int(delta.total_seconds() / 60)
        db.commit()
        db.refresh(workout)
    return workout


@contextmanager
def assert_query_count(max_queries: int):
    """
    Context manager to assert maximum query count.
    
    Usage:
        with assert_query_count(2):
            response = client.get("/api/v1/workouts")
    
    This helps prevent N+1 queries by enforcing query limits in tests.
    """
    query_count = [0]  # Use list to allow modification in nested scope
    
    def count_queries(conn, cursor, statement, parameters, context, executemany):
        query_count[0] += 1
    
    # Attach listener
    event.listen(Engine, "before_cursor_execute", count_queries)
    
    try:
        yield
        assert query_count[0] <= max_queries, \
            f"Expected ≤{max_queries} queries, got {query_count[0]}"
    finally:
        # Remove listener
        event.remove(Engine, "before_cursor_execute", count_queries)
