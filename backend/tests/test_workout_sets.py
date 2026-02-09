"""
Integration tests for workout set operations.
"""
import pytest
from uuid import uuid4
from fastapi import status
from app.utils.enums import SetType, RPE

def test_add_set_to_exercise(client, db, test_user, test_exercise, auth_headers):
    """Test adding set to exercise."""
    # Start workout and add exercise
    response = client.post(
        "/api/v1/workouts/start",
        headers=auth_headers
    )
    workout_id = response.json()["id"]
    
    response = client.post(
        f"/api/v1/workouts/{workout_id}/exercises",
        json={"exercise_id": str(test_exercise.id)},
        headers=auth_headers
    )
    workout_exercise_id = response.json()["exercises"][0]["id"]
    
    # Add set
    response = client.post(
        f"/api/v1/workout-exercises/{workout_exercise_id}/sets",
        json={
            "reps": 8,
            "weight": 60.0,
            "set_type": SetType.WORKING.value,
            "rpe": RPE.MEDIUM.value
        },
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verify set data
    assert data["reps"] == 8
    assert data["weight"] == 60.0
    assert data["set_type"] == SetType.WORKING.value
    assert data["rpe"] == RPE.MEDIUM.value
    assert data["set_number"] == 0  # First set = 0


def test_update_set(client, db, test_user, test_exercise, auth_headers):
    """Test updating set."""
    # Setup: workout, exercise, set
    response = client.post(
        "/api/v1/workouts/start",
        headers=auth_headers
    )
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
    set_id = response.json()["id"]
    
    # Update set
    response = client.patch(
        f"/api/v1/sets/{set_id}",
        json={"reps": 10, "weight": 65.0},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verify update
    assert data["reps"] == 10
    assert data["weight"] == 65.0
    assert data["set_type"] == SetType.WORKING.value  # Unchanged


def test_delete_set(client, db, test_user, test_exercise, auth_headers):
    """Test deleting set."""
    # Setup: workout, exercise, set
    response = client.post(
        "/api/v1/workouts/start",
        headers=auth_headers
    )
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
    set_id = response.json()["id"]
    
    # Delete set
    response = client.delete(
        f"/api/v1/sets/{set_id}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify set deleted (get workout, check sets)
    response = client.get(
        f"/api/v1/workouts/active",
        headers=auth_headers
    )
    workout = response.json()
    exercise = workout["exercises"][0]
    assert len(exercise["sets"]) == 0


def test_set_number_auto_increment(client, db, test_user, test_exercise, auth_headers):
    """Test that set_number auto-increments correctly (0-based: 0, 1, 2)."""
    # Setup: workout, exercise
    response = client.post(
        "/api/v1/workouts/start",
        headers=auth_headers
    )
    workout_id = response.json()["id"]
    
    response = client.post(
        f"/api/v1/workouts/{workout_id}/exercises",
        json={"exercise_id": str(test_exercise.id)},
        headers=auth_headers
    )
    workout_exercise_id = response.json()["exercises"][0]["id"]
    
    # Add multiple sets without set_number
    set_ids = []
    for i in range(3):
        response = client.post(
            f"/api/v1/workout-exercises/{workout_exercise_id}/sets",
            json={"reps": 8, "weight": 60.0, "set_type": SetType.WORKING.value},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["set_number"] == i  # 0, 1, 2
        set_ids.append(response.json()["id"])
    
    # Test: delete middle set (set_number=1), then add new set
    # ⚠️ LOCKED: Backend MUST implement monotonic increment (do NOT reuse set_number)
    # Expected: new set should get set_number=3 (monotonic increment)
    # NOT: set_number=1 (reusing deleted number)
    # Why: Avoids conflicts with offline queue + optimistic UI
    #
    # ⚠️ CRITICAL: Before running this test, confirm your backend create-set logic:
    # ✅ CORRECT: new_set_number = max(existing_set_numbers) + 1
    #    OR: new_set_number = count_all_sets_ever_created (monotonic)
    # ❌ WRONG: "lowest available gap" (gap-based reuse)
    #
    # If backend is gap-based today, the test will fail — not because the test is wrong,
    # but because backend behavior doesn't match your locked spec.
    # Fix backend first, then run test.
    response = client.delete(
        f"/api/v1/sets/{set_ids[1]}",  # Delete middle set (set_number=1)
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Add new set
    response = client.post(
        f"/api/v1/workout-exercises/{workout_exercise_id}/sets",
        json={"reps": 8, "weight": 60.0, "set_type": SetType.WORKING.value},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    new_set_number = response.json()["set_number"]
    
    # ⚠️ LOCKED: Strict assertion (monotonic increment)
    # Confirm backend implements this before running test, otherwise test will fail
    # and you'll waste time debugging a "design mismatch"
    assert new_set_number == 3, (
        f"Expected set_number=3 (monotonic increment), got {new_set_number}. "
        "Backend must NOT reuse deleted set numbers. "
        "Check backend logic: should use max(existing) + 1, NOT gap-based reuse."
    )
