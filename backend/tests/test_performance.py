"""
Performance tests: Query count checks to prevent N+1 queries.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime, timedelta, timezone

from app.models.user import User
from app.models.workout import Workout, LifecycleStatus, CompletionStatus
from app.models.exercise import ExerciseLibrary
from app.models.workout import WorkoutExercise, WorkoutSet
from app.utils.auth import create_access_token
from tests.helpers import assert_query_count


@pytest.fixture
def test_user_with_workouts(db: Session) -> User:
    """Create a test user with multiple finalized workouts."""
    user = User(
        id=uuid4(),
        email="perfuser@example.com",
        password_hash="hashed",
        units="kg",
        timezone="Asia/Kolkata",
        default_rest_timer_seconds=90
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create 10 finalized workouts
    for i in range(10):
        workout = Workout(
            id=uuid4(),
            user_id=user.id,
            lifecycle_status=LifecycleStatus.FINALIZED.value,
            completion_status=CompletionStatus.COMPLETED.value,
            start_time=datetime.now(timezone.utc) - timedelta(days=i),
            end_time=datetime.now(timezone.utc) - timedelta(days=i) + timedelta(hours=1),
            duration_minutes=60
        )
        db.add(workout)
    db.commit()
    
    return user


@pytest.fixture
def test_user_with_workout_detail(db: Session) -> tuple[User, Workout]:
    """Create a test user with a workout that has exercises and sets."""
    user = User(
        id=uuid4(),
        email="detailuser@example.com",
        password_hash="hashed",
        units="kg",
        timezone="Asia/Kolkata",
        default_rest_timer_seconds=90
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create exercise
    exercise = ExerciseLibrary(
        id=uuid4(),
        name="Bench Press",
        primary_muscle_group="chest",
        equipment="barbell",
        movement_type="push",
        normalized_name="bench press"
    )
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    
    # Create workout
    workout = Workout(
        id=uuid4(),
        user_id=user.id,
        lifecycle_status=LifecycleStatus.FINALIZED.value,
        completion_status=CompletionStatus.COMPLETED.value,
        start_time=datetime.now(timezone.utc) - timedelta(hours=1),
        end_time=datetime.now(timezone.utc),
        duration_minutes=60
    )
    db.add(workout)
    db.commit()
    db.refresh(workout)
    
    # Add exercise to workout
    workout_exercise = WorkoutExercise(
        id=uuid4(),
        workout_id=workout.id,
        exercise_id=exercise.id,
        order_index=0
    )
    db.add(workout_exercise)
    db.commit()
    db.refresh(workout_exercise)
    
    # Add sets
    for i in range(3):
        workout_set = WorkoutSet(
            id=uuid4(),
            workout_exercise_id=workout_exercise.id,
            set_number=i + 1,
            weight=100.0,
            reps=10,
            set_type="working"
        )
        db.add(workout_set)
    db.commit()
    
    return user, workout


def test_history_endpoint_query_count(client: TestClient, db: Session, test_user_with_workouts: User):
    """Test workout history endpoint uses ≤2 queries (no N+1)."""
    token = create_access_token(test_user_with_workouts.id)
    
    with assert_query_count(2):  # 1 for workouts, 1 for user (if needed)
        response = client.get(
            "/api/v1/workouts",
            headers={"Authorization": f"Bearer {token}"}
        )
    assert response.status_code == 200


def test_workout_detail_query_count(client: TestClient, db: Session, test_user_with_workout_detail: tuple[User, Workout]):
    """Test workout detail endpoint uses ≤10 queries (acceptable, not N+1)."""
    user, workout = test_user_with_workout_detail
    token = create_access_token(user.id)
    
    with assert_query_count(10):  # Acceptable query count (includes workout, exercises, sets, exercise library lookups)
        response = client.get(
            f"/api/v1/workouts/{workout.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
    assert response.status_code == 200


def test_active_workout_query_count(client: TestClient, db: Session, test_user: User):
    """Test active workout endpoint uses ≤2 queries."""
    token = create_access_token(test_user.id)
    
    with assert_query_count(2):  # 1 for workout query, 1 for user (if needed)
        response = client.get(
            "/api/v1/workouts/active",
            headers={"Authorization": f"Bearer {token}"}
        )
    assert response.status_code == 200


def test_user_profile_query_count(client: TestClient, db: Session, test_user: User):
    """Test user profile endpoint uses ≤1 query."""
    token = create_access_token(test_user.id)
    
    with assert_query_count(1):
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
    assert response.status_code == 200
