"""
Integration tests for workout update and session endpoints.
"""
import pytest
from uuid import uuid4
from fastapi import status
from app.models.user import User
from app.models.exercise import ExerciseLibrary
from app.utils.enums import LifecycleStatus, CompletionStatus, SetType


def test_update_workout_name(client, db, test_user, test_exercise, auth_headers):
    """Test updating workout name."""
    # Start workout
    response = client.post(
        "/api/v1/workouts/start",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    workout_id = response.json()["id"]
    
    # Update name
    response = client.patch(
        f"/api/v1/workouts/{workout_id}",
        json={"name": "Morning Workout"},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verify name updated
    assert data["name"] == "Morning Workout"
    assert data["id"] == workout_id


def test_update_workout_notes(client, db, test_user, test_exercise, auth_headers):
    """Test updating workout notes."""
    # Start workout
    response = client.post(
        "/api/v1/workouts/start",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    workout_id = response.json()["id"]
    
    # Update notes
    response = client.patch(
        f"/api/v1/workouts/{workout_id}",
        json={"notes": "Great session today!"},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verify notes updated
    assert data["notes"] == "Great session today!"
    assert data["id"] == workout_id


def test_update_workout_name_and_notes(client, db, test_user, test_exercise, auth_headers):
    """Test updating both name and notes."""
    # Start workout
    response = client.post(
        "/api/v1/workouts/start",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    workout_id = response.json()["id"]
    
    # Update both
    response = client.patch(
        f"/api/v1/workouts/{workout_id}",
        json={
            "name": "Evening Workout",
            "notes": "Feeling strong today!"
        },
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verify both updated
    assert data["name"] == "Evening Workout"
    assert data["notes"] == "Feeling strong today!"


def test_update_workout_clear_notes(client, db, test_user, test_exercise, auth_headers):
    """Test clearing notes with empty string."""
    # Start workout and set notes
    response = client.post(
        "/api/v1/workouts/start",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    workout_id = response.json()["id"]
    
    # Set notes first
    response = client.patch(
        f"/api/v1/workouts/{workout_id}",
        json={"notes": "Some notes"},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["notes"] == "Some notes"
    
    # Clear notes with empty string
    response = client.patch(
        f"/api/v1/workouts/{workout_id}",
        json={"notes": ""},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verify notes cleared (None)
    assert data["notes"] is None


def test_update_workout_draft_only(client, db, test_user, test_exercise, auth_headers):
    """Test that cannot update finalized workout."""
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
    
    # Finish workout
    response = client.post(
        f"/api/v1/workouts/{workout_id}/finish",
        json={"completion_status": CompletionStatus.COMPLETED.value},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    
    # Try to update finalized workout
    response = client.patch(
        f"/api/v1/workouts/{workout_id}",
        json={"name": "Updated Name"},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Cannot modify finalized workout" in response.json()["detail"]


def test_get_workout_session_success(client, db, test_user, test_exercise, auth_headers):
    """Test getting workout session by ID."""
    # Start workout and add exercise
    response = client.post("/api/v1/workouts/start", headers=auth_headers)
    workout_id = response.json()["id"]
    
    response = client.post(
        f"/api/v1/workouts/{workout_id}/exercises",
        json={"exercise_id": str(test_exercise.id)},
        headers=auth_headers
    )
    
    # Get session
    response = client.get(
        f"/api/v1/workouts/{workout_id}/session",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verify workout returned
    assert data["id"] == workout_id
    assert data["lifecycle_status"] == LifecycleStatus.DRAFT.value
    assert len(data["exercises"]) == 1


def test_get_workout_session_finalized(client, db, test_user, test_exercise, auth_headers):
    """Test that cannot get session for finalized workout (returns 404)."""
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
    
    # Finish workout
    response = client.post(
        f"/api/v1/workouts/{workout_id}/finish",
        json={"completion_status": CompletionStatus.COMPLETED.value},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    
    # Try to get session for finalized workout (should return 404, not 400)
    response = client.get(
        f"/api/v1/workouts/{workout_id}/session",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_workout_session_wrong_user(client, db, test_user, test_exercise, auth_headers):
    """Test that getting session for other user's workout returns 404 (not 403)."""
    # Create another user
    other_user = User(
        id=uuid4(),
        email="other@example.com",
        password_hash="hashed",
        units="kg",
        timezone="UTC"
    )
    db.add(other_user)
    db.commit()
    
    # Start workout as other user (manually create)
    from app.models.workout import Workout
    from app.utils.enums import LifecycleStatus
    other_workout = Workout(
        id=uuid4(),
        user_id=other_user.id,
        lifecycle_status=LifecycleStatus.DRAFT.value
    )
    db.add(other_workout)
    db.commit()
    
    # Try to get session for other user's workout (should return 404, not 403)
    response = client.get(
        f"/api/v1/workouts/{other_workout.id}/session",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    # Verify it says "not found" not "not authorized" (security)
    assert "not found" in response.json()["detail"].lower()
