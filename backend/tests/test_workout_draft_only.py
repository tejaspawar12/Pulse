"""
Integration tests for draft-only modification rules.
"""
import pytest
from uuid import uuid4
from fastapi import status
from app.models.user import User
from tests.helpers import finalize_workout  # ⚠️ LOCKED: ONLY import from helpers.py

def test_cannot_modify_finalized_workout(client, db, test_user, test_exercise, auth_headers):
    """Test that cannot add/edit/delete in finalized workout."""
    # Start workout, add exercise, add set
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
        json={"reps": 8, "weight": 60.0, "set_type": "working"},
        headers=auth_headers
    )
    set_id = response.json()["id"]
    
    # Finalize workout
    finalize_workout(db, workout_id)
    
    # Try to add exercise → should fail
    response = client.post(
        f"/api/v1/workouts/{workout_id}/exercises",
        json={"exercise_id": str(test_exercise.id)},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    # Try to edit set → should fail
    response = client.patch(
        f"/api/v1/sets/{set_id}",
        json={"reps": 10},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    # Try to delete set → should fail
    response = client.delete(f"/api/v1/sets/{set_id}", headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_cannot_modify_other_user_workout(client, db, test_user, test_exercise, auth_headers):
    """Test that cannot modify another user's workout."""
    # Create other user
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
    other_auth_headers = {"X-DEV-USER-ID": str(other_user.id)}
    
    # Other user starts workout, adds exercise, adds set
    response = client.post("/api/v1/workouts/start", headers=other_auth_headers)
    workout_id = response.json()["id"]
    
    response = client.post(
        f"/api/v1/workouts/{workout_id}/exercises",
        json={"exercise_id": str(test_exercise.id)},
        headers=other_auth_headers
    )
    workout_exercise_id = response.json()["exercises"][0]["id"]
    
    response = client.post(
        f"/api/v1/workout-exercises/{workout_exercise_id}/sets",
        json={"reps": 8, "weight": 60.0, "set_type": "working"},
        headers=other_auth_headers
    )
    set_id = response.json()["id"]
    
    # Try to modify as test_user → should fail with 403
    response = client.post(
        f"/api/v1/workouts/{workout_id}/exercises",
        json={"exercise_id": str(test_exercise.id)},
        headers=auth_headers  # test_user's headers
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    response = client.patch(
        f"/api/v1/sets/{set_id}",
        json={"reps": 10},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    response = client.delete(f"/api/v1/sets/{set_id}", headers=auth_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
