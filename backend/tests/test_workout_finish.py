"""
Integration tests for finish workout endpoint.
"""
import pytest
from uuid import uuid4
from fastapi import status
from app.models.user import User
from app.models.exercise import ExerciseLibrary
from app.utils.enums import CompletionStatus, SetType, LifecycleStatus


def test_finish_workout_success(client, db, test_user, test_exercise, auth_headers):
    """Test finishing workout successfully."""
    # Start workout and add exercise with sets
    response = client.post(
        "/api/v1/workouts/start",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    workout_id = response.json()["id"]
    
    # Add exercise
    response = client.post(
        f"/api/v1/workouts/{workout_id}/exercises",
        json={"exercise_id": str(test_exercise.id)},
        headers=auth_headers
    )
    workout_exercise_id = response.json()["exercises"][0]["id"]
    
    # Add set
    response = client.post(
        f"/api/v1/workout-exercises/{workout_exercise_id}/sets",
        json={"reps": 8, "weight": 60.0, "set_type": SetType.WORKING.value},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    
    # Finish workout
    response = client.post(
        f"/api/v1/workouts/{workout_id}/finish",
        json={
            "completion_status": CompletionStatus.COMPLETED.value,
            "notes": "Great workout!"
        },
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verify workout finalized
    assert data["lifecycle_status"] == LifecycleStatus.FINALIZED.value
    assert data["completion_status"] == CompletionStatus.COMPLETED.value
    assert data["notes"] == "Great workout!"
    assert data["end_time"] is not None
    assert data["duration_minutes"] is not None
    assert data["duration_minutes"] >= 0  # Can be 0 if workout finishes instantly in tests


def test_finish_workout_idempotent(client, db, test_user, test_exercise, auth_headers):
    """Test that finishing already-finalized workout returns existing (idempotent)."""
    # Start workout, add exercise, add set, finish
    response = client.post("/api/v1/workouts/start", headers=auth_headers)
    workout_id = response.json()["id"]
    
    response = client.post(
        f"/api/v1/workouts/{workout_id}/exercises",
        json={"exercise_id": str(test_exercise.id)},
        headers=auth_headers
    )
    workout_exercise_id = response.json()["exercises"][0]["id"]
    
    response = client.post(
        f"/api/v1/workout-exercises/{workout_exercise_id}/sets",
        json={"reps": 8, "weight": 60.0, "set_type": SetType.WORKING.value},
        headers=auth_headers
    )
    
    # Finish workout first time
    response = client.post(
        f"/api/v1/workouts/{workout_id}/finish",
        json={"completion_status": CompletionStatus.COMPLETED.value},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    first_finish = response.json()
    
    # Try to finish again (idempotent)
    response = client.post(
        f"/api/v1/workouts/{workout_id}/finish",
        json={"completion_status": CompletionStatus.COMPLETED.value},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    second_finish = response.json()
    
    # Verify same workout returned (idempotent)
    assert first_finish["id"] == second_finish["id"]
    assert first_finish["lifecycle_status"] == second_finish["lifecycle_status"]
    assert first_finish["end_time"] == second_finish["end_time"]


def test_finish_workout_abandoned(client, db, test_user, test_exercise, auth_headers):
    """Test that cannot finish abandoned workout."""
    # Start workout
    response = client.post("/api/v1/workouts/start", headers=auth_headers)
    workout_id = response.json()["id"]
    
    # Abandon workout (manually set status)
    from app.models.workout import Workout
    workout = db.query(Workout).filter(Workout.id == workout_id).first()
    workout.lifecycle_status = LifecycleStatus.ABANDONED.value
    workout.completion_status = None
    db.commit()
    db.flush()  # Ensure session state is updated
    
    # Try to finish abandoned workout
    response = client.post(
        f"/api/v1/workouts/{workout_id}/finish",
        json={"completion_status": CompletionStatus.COMPLETED.value},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Cannot finish abandoned workout" in response.json()["detail"]


def test_finish_workout_no_sets_completed(client, db, test_user, test_exercise, auth_headers):
    """Test that cannot finish workout with 0 sets and completed status."""
    # Start workout and add exercise (no sets)
    response = client.post("/api/v1/workouts/start", headers=auth_headers)
    workout_id = response.json()["id"]
    
    response = client.post(
        f"/api/v1/workouts/{workout_id}/exercises",
        json={"exercise_id": str(test_exercise.id)},
        headers=auth_headers
    )
    
    # Try to finish with completed status (should fail)
    response = client.post(
        f"/api/v1/workouts/{workout_id}/finish",
        json={"completion_status": CompletionStatus.COMPLETED.value},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "no sets" in response.json()["detail"].lower()


def test_finish_workout_no_sets_partial(client, db, test_user, test_exercise, auth_headers):
    """Test that can finish workout with 0 sets if status is partial."""
    # Start workout and add exercise (no sets)
    response = client.post("/api/v1/workouts/start", headers=auth_headers)
    workout_id = response.json()["id"]
    
    response = client.post(
        f"/api/v1/workouts/{workout_id}/exercises",
        json={"exercise_id": str(test_exercise.id)},
        headers=auth_headers
    )
    
    # Finish with partial status (should succeed)
    response = client.post(
        f"/api/v1/workouts/{workout_id}/finish",
        json={"completion_status": CompletionStatus.PARTIAL.value},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["completion_status"] == CompletionStatus.PARTIAL.value


def test_finish_workout_daily_training_state(client, db, test_user, test_exercise, auth_headers):
    """Test that daily_training_state is written correctly."""
    from app.models.daily_training_state import DailyTrainingState
    from app.models.workout import Workout
    from datetime import date
    from sqlalchemy import text
    
    # Start workout, add exercise, add set, finish
    response = client.post("/api/v1/workouts/start", headers=auth_headers)
    workout_id = response.json()["id"]
    
    response = client.post(
        f"/api/v1/workouts/{workout_id}/exercises",
        json={"exercise_id": str(test_exercise.id)},
        headers=auth_headers
    )
    workout_exercise_id = response.json()["exercises"][0]["id"]
    
    response = client.post(
        f"/api/v1/workout-exercises/{workout_exercise_id}/sets",
        json={"reps": 8, "weight": 60.0, "set_type": SetType.WORKING.value},
        headers=auth_headers
    )
    
    # Get workout to calculate expected date
    workout = db.query(Workout).filter(Workout.id == workout_id).first()
    user_timezone = test_user.timezone or "Asia/Kolkata"
    
    # Calculate expected date using same logic as service
    date_query = text(
        "SELECT DATE(start_time AT TIME ZONE :tz) as workout_date "
        "FROM workouts WHERE id = :workout_id"
    )
    result = db.execute(
        date_query,
        {"tz": user_timezone, "workout_id": workout_id}
    ).fetchone()
    expected_date = result.workout_date if result else None
    
    # Finish workout
    response = client.post(
        f"/api/v1/workouts/{workout_id}/finish",
        json={"completion_status": CompletionStatus.COMPLETED.value},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    
    # Verify daily_training_state written (filter by both user_id AND date for safety)
    daily_state = (
        db.query(DailyTrainingState)
        .filter(
            DailyTrainingState.user_id == test_user.id,
            DailyTrainingState.date == expected_date
        )
        .first()
    )
    
    assert daily_state is not None, "daily_training_state should be created"
    assert daily_state.worked_out is True
    # workout_id from response is string, daily_state.workout_id is UUID - convert for comparison
    assert str(daily_state.workout_id) == str(workout_id)
    assert isinstance(daily_state.date, date)
    assert daily_state.date == expected_date
    
    # Verify only one entry for this user+date (upsert worked correctly)
    count = (
        db.query(DailyTrainingState)
        .filter(
            DailyTrainingState.user_id == test_user.id,
            DailyTrainingState.date == expected_date
        )
        .count()
    )
    assert count == 1, "Should have exactly one daily_training_state entry per user+date"
