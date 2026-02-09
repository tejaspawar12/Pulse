"""
Integration tests for workout exercise operations.
"""
import pytest
from uuid import uuid4
from fastapi import status
from app.models.user import User
from tests.helpers import finalize_workout  # ⚠️ LOCKED: ONLY import from helpers.py

def test_add_exercise_to_workout(client, db, test_user, test_exercise, auth_headers):
    """Test adding exercise to workout."""
    # Start workout
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
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verify workout has exercise
    assert len(data["exercises"]) == 1
    assert data["exercises"][0]["exercise_id"] == str(test_exercise.id)
    assert data["exercises"][0]["exercise_name"] == "Bench Press"
    assert data["exercises"][0]["order_index"] == 0


def test_add_exercise_to_finalized_workout(client, db, test_user, test_exercise, auth_headers):
    """Test that cannot add exercise to finalized workout."""
    # Start workout
    response = client.post(
        "/api/v1/workouts/start",
        headers=auth_headers
    )
    workout_id = response.json()["id"]
    
    # Finalize workout using helper (sets all required fields)
    finalize_workout(db, workout_id)
    
    # Try to add exercise
    response = client.post(
        f"/api/v1/workouts/{workout_id}/exercises",
        json={"exercise_id": str(test_exercise.id)},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Cannot modify finalized workout" in response.json()["detail"]


def test_add_exercise_to_other_user_workout(client, db, test_user, test_exercise, auth_headers):
    """Test that cannot add exercise to another user's workout."""
    # Create second user using SAME db fixture
    # Note: User is imported at top of file
    other_user = User(
        id=uuid4(),
        email="other@example.com",
        password_hash="hashed",
        units="kg",
        timezone="UTC"
    )
    db.add(other_user)
    db.commit()
    db.refresh(other_user)
    
    # Start workout for other user
    other_auth_headers = {"X-DEV-USER-ID": str(other_user.id)}
    response = client.post(
        "/api/v1/workouts/start",
        headers=other_auth_headers
    )
    workout_id = response.json()["id"]
    
    # Try to add exercise as test_user (should fail with 403)
    response = client.post(
        f"/api/v1/workouts/{workout_id}/exercises",
        json={"exercise_id": str(test_exercise.id)},
        headers=auth_headers  # Using test_user's headers
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Not authorized" in response.json()["detail"]
