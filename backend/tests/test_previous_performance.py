"""
Integration tests for previous performance endpoint.
"""
import pytest
from uuid import uuid4
from fastapi import status
from datetime import datetime, timezone, timedelta
from app.models.user import User
from app.models.exercise import ExerciseLibrary
from app.models.workout import Workout, WorkoutExercise, WorkoutSet
from app.utils.enums import LifecycleStatus, CompletionStatus, SetType


def test_get_last_performance_success(client, db, test_user, test_exercise, auth_headers):
    """Test getting last performance for logged exercise."""
    # Create finalized workout with exercise and sets
    workout = Workout(
        id=uuid4(),
        user_id=test_user.id,
        start_time=datetime.now(timezone.utc) - timedelta(days=1),
        lifecycle_status=LifecycleStatus.FINALIZED.value,
        completion_status=CompletionStatus.COMPLETED.value,
        end_time=datetime.now(timezone.utc) - timedelta(days=1) + timedelta(hours=1)
    )
    db.add(workout)
    db.flush()
    
    workout_exercise = WorkoutExercise(
        id=uuid4(),
        workout_id=workout.id,
        exercise_id=test_exercise.id,
        order_index=0
    )
    db.add(workout_exercise)
    db.flush()
    
    # Add sets
    set1 = WorkoutSet(
        id=uuid4(),
        workout_exercise_id=workout_exercise.id,
        set_number=1,
        reps=8,
        weight=60.0,
        set_type=SetType.WORKING.value
    )
    set2 = WorkoutSet(
        id=uuid4(),
        workout_exercise_id=workout_exercise.id,
        set_number=2,
        reps=8,
        weight=60.0,
        set_type=SetType.WORKING.value
    )
    db.add(set1)
    db.add(set2)
    db.commit()
    
    # Get last performance
    response = client.get(
        f"/api/v1/users/me/exercises/{test_exercise.id}/last-performance",
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verify response structure
    assert "last_date" in data
    assert "sets" in data
    assert len(data["sets"]) == 2
    
    # Verify sets are in correct order
    assert data["sets"][0]["set_number"] == 1
    assert data["sets"][1]["set_number"] == 2
    
    # Verify set data
    assert data["sets"][0]["reps"] == 8
    assert data["sets"][0]["weight"] == 60.0
    assert data["sets"][1]["reps"] == 8
    assert data["sets"][1]["weight"] == 60.0


def test_get_last_performance_not_found(client, db, test_user, auth_headers):
    """Test 404 for never-logged exercise."""
    new_exercise_id = uuid4()
    
    response = client.get(
        f"/api/v1/users/me/exercises/{new_exercise_id}/last-performance",
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "No previous performance found" in response.json()["detail"]


def test_get_last_performance_only_finalized(client, db, test_user, test_exercise, auth_headers):
    """Test that only finalized workouts are included."""
    # Create draft workout with exercise
    draft_workout = Workout(
        id=uuid4(),
        user_id=test_user.id,
        start_time=datetime.now(timezone.utc) - timedelta(days=2),
        lifecycle_status=LifecycleStatus.DRAFT.value
    )
    db.add(draft_workout)
    db.flush()
    
    draft_exercise = WorkoutExercise(
        id=uuid4(),
        workout_id=draft_workout.id,
        exercise_id=test_exercise.id,
        order_index=0
    )
    db.add(draft_exercise)
    db.flush()
    
    draft_set = WorkoutSet(
        id=uuid4(),
        workout_exercise_id=draft_exercise.id,
        set_number=1,
        reps=10,
        weight=50.0,
        set_type=SetType.WORKING.value
    )
    db.add(draft_set)
    db.commit()
    
    # Create finalized workout with same exercise (more recent)
    finalized_workout = Workout(
        id=uuid4(),
        user_id=test_user.id,
        start_time=datetime.now(timezone.utc) - timedelta(days=1),
        lifecycle_status=LifecycleStatus.FINALIZED.value,
        completion_status=CompletionStatus.COMPLETED.value,
        end_time=datetime.now(timezone.utc) - timedelta(days=1) + timedelta(hours=1)
    )
    db.add(finalized_workout)
    db.flush()
    
    finalized_exercise = WorkoutExercise(
        id=uuid4(),
        workout_id=finalized_workout.id,
        exercise_id=test_exercise.id,
        order_index=0
    )
    db.add(finalized_exercise)
    db.flush()
    
    finalized_set = WorkoutSet(
        id=uuid4(),
        workout_exercise_id=finalized_exercise.id,
        set_number=1,
        reps=8,
        weight=60.0,
        set_type=SetType.WORKING.value
    )
    db.add(finalized_set)
    db.commit()
    
    # Get last performance - should return finalized workout (not draft)
    response = client.get(
        f"/api/v1/users/me/exercises/{test_exercise.id}/last-performance",
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verify it returns finalized workout data (8 reps, 60kg)
    assert len(data["sets"]) == 1
    assert data["sets"][0]["reps"] == 8
    assert data["sets"][0]["weight"] == 60.0


def test_get_last_performance_most_recent(client, db, test_user, test_exercise, auth_headers):
    """Test that most recent workout is returned."""
    # Create older finalized workout
    older_workout = Workout(
        id=uuid4(),
        user_id=test_user.id,
        start_time=datetime.now(timezone.utc) - timedelta(days=5),
        lifecycle_status=LifecycleStatus.FINALIZED.value,
        completion_status=CompletionStatus.COMPLETED.value,
        end_time=datetime.now(timezone.utc) - timedelta(days=5) + timedelta(hours=1)
    )
    db.add(older_workout)
    db.flush()
    
    older_exercise = WorkoutExercise(
        id=uuid4(),
        workout_id=older_workout.id,
        exercise_id=test_exercise.id,
        order_index=0
    )
    db.add(older_exercise)
    db.flush()
    
    older_set = WorkoutSet(
        id=uuid4(),
        workout_exercise_id=older_exercise.id,
        set_number=1,
        reps=5,
        weight=50.0,
        set_type=SetType.WORKING.value
    )
    db.add(older_set)
    db.commit()
    
    # Create newer finalized workout
    newer_workout = Workout(
        id=uuid4(),
        user_id=test_user.id,
        start_time=datetime.now(timezone.utc) - timedelta(days=1),
        lifecycle_status=LifecycleStatus.FINALIZED.value,
        completion_status=CompletionStatus.COMPLETED.value,
        end_time=datetime.now(timezone.utc) - timedelta(days=1) + timedelta(hours=1)
    )
    db.add(newer_workout)
    db.flush()
    
    newer_exercise = WorkoutExercise(
        id=uuid4(),
        workout_id=newer_workout.id,
        exercise_id=test_exercise.id,
        order_index=0
    )
    db.add(newer_exercise)
    db.flush()
    
    newer_set = WorkoutSet(
        id=uuid4(),
        workout_exercise_id=newer_exercise.id,
        set_number=1,
        reps=8,
        weight=60.0,
        set_type=SetType.WORKING.value
    )
    db.add(newer_set)
    db.commit()
    
    # Get last performance - should return newer workout
    response = client.get(
        f"/api/v1/users/me/exercises/{test_exercise.id}/last-performance",
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verify it returns newer workout data (8 reps, 60kg)
    assert len(data["sets"]) == 1
    assert data["sets"][0]["reps"] == 8
    assert data["sets"][0]["weight"] == 60.0


def test_get_last_performance_excludes_abandoned(client, db, test_user, test_exercise, auth_headers):
    """Test that abandoned workouts are excluded."""
    # Create abandoned workout
    abandoned_workout = Workout(
        id=uuid4(),
        user_id=test_user.id,
        start_time=datetime.now(timezone.utc) - timedelta(days=2),
        lifecycle_status=LifecycleStatus.ABANDONED.value
    )
    db.add(abandoned_workout)
    db.flush()
    
    abandoned_exercise = WorkoutExercise(
        id=uuid4(),
        workout_id=abandoned_workout.id,
        exercise_id=test_exercise.id,
        order_index=0
    )
    db.add(abandoned_exercise)
    db.flush()
    
    abandoned_set = WorkoutSet(
        id=uuid4(),
        workout_exercise_id=abandoned_exercise.id,
        set_number=1,
        reps=10,
        weight=50.0,
        set_type=SetType.WORKING.value
    )
    db.add(abandoned_set)
    db.commit()
    
    # Create finalized workout with same exercise
    finalized_workout = Workout(
        id=uuid4(),
        user_id=test_user.id,
        start_time=datetime.now(timezone.utc) - timedelta(days=1),
        lifecycle_status=LifecycleStatus.FINALIZED.value,
        completion_status=CompletionStatus.COMPLETED.value,
        end_time=datetime.now(timezone.utc) - timedelta(days=1) + timedelta(hours=1)
    )
    db.add(finalized_workout)
    db.flush()
    
    finalized_exercise = WorkoutExercise(
        id=uuid4(),
        workout_id=finalized_workout.id,
        exercise_id=test_exercise.id,
        order_index=0
    )
    db.add(finalized_exercise)
    db.flush()
    
    finalized_set = WorkoutSet(
        id=uuid4(),
        workout_exercise_id=finalized_exercise.id,
        set_number=1,
        reps=8,
        weight=60.0,
        set_type=SetType.WORKING.value
    )
    db.add(finalized_set)
    db.commit()
    
    # Get last performance - should return finalized workout (not abandoned)
    response = client.get(
        f"/api/v1/users/me/exercises/{test_exercise.id}/last-performance",
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verify it returns finalized workout data (8 reps, 60kg)
    assert len(data["sets"]) == 1
    assert data["sets"][0]["reps"] == 8
    assert data["sets"][0]["weight"] == 60.0
