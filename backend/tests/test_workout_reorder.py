"""
Integration tests for exercise reordering.
"""
import pytest
from uuid import uuid4
from fastapi import status

def test_reorder_exercises_success(client, db, test_user, test_exercise, auth_headers):
    """Test reordering exercises successfully."""
    # Create second exercise using SAME db fixture
    from app.models.exercise import ExerciseLibrary
    exercise2 = ExerciseLibrary(
        id=uuid4(),
        name="Squat",
        primary_muscle_group="legs",
        equipment="barbell",
        movement_type="compound",
        normalized_name="squat"
    )
    db.add(exercise2)
    db.commit()
    db.refresh(exercise2)
    
    # Start workout and add two exercises
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
    exercise1_id = response.json()["exercises"][0]["id"]
    
    response = client.post(
        f"/api/v1/workouts/{workout_id}/exercises",
        json={"exercise_id": str(exercise2.id)},
        headers=auth_headers
    )
    exercise2_id = response.json()["exercises"][1]["id"]
    
    # Reorder: swap positions
    response = client.patch(
        f"/api/v1/workouts/{workout_id}/exercises/reorder",
        json={
            "items": [
                {"workout_exercise_id": str(exercise2_id), "order_index": 0},
                {"workout_exercise_id": str(exercise1_id), "order_index": 1}
            ]
        },
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verify order changed - use order_index mapping (not list position)
    by_id = {e["id"]: e["order_index"] for e in data["exercises"]}
    assert by_id[str(exercise2_id)] == 0
    assert by_id[str(exercise1_id)] == 1
    assert len(data["exercises"]) == 2


def test_reorder_exercises_non_sequential(client, db, test_user, test_exercise, auth_headers):
    """Test that non-sequential order_index returns 400."""
    # Setup: workout with exercise
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
    exercise_id = response.json()["exercises"][0]["id"]
    
    # Try to reorder with non-sequential order_index
    response = client.patch(
        f"/api/v1/workouts/{workout_id}/exercises/reorder",
        json={
            "items": [
                {"workout_exercise_id": str(exercise_id), "order_index": 5}  # Should be 0
            ]
        },
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "sequential" in response.json()["detail"].lower()


def test_reorder_exercises_missing_exercise(client, db, test_user, test_exercise, auth_headers):
    """
    Test that missing an exercise returns 400 (must include all exercises).
    
    ⚠️ NOTE: This test assumes backend validation exists.
    If your backend currently allows partial reorder, either:
    1. Implement validation in backend (recommended)
    2. OR change test to match current behavior and add validation in error-handling section
    
    For production-grade reorder, you should enforce:
    - All workout_exercise_ids must be included
    - order_index must be exactly 0..n-1 unique
    """
    # Setup: workout with two exercises
    from app.models.exercise import ExerciseLibrary
    exercise2 = ExerciseLibrary(
        id=uuid4(),
        name="Squat",
        primary_muscle_group="legs",
        equipment="barbell",
        movement_type="compound",
        normalized_name="squat"
    )
    db.add(exercise2)
    db.commit()
    
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
    exercise1_id = response.json()["exercises"][0]["id"]
    
    response = client.post(
        f"/api/v1/workouts/{workout_id}/exercises",
        json={"exercise_id": str(exercise2.id)},
        headers=auth_headers
    )
    exercise2_id = response.json()["exercises"][1]["id"]
    
    # Try to reorder with only one exercise (missing the other)
    response = client.patch(
        f"/api/v1/workouts/{workout_id}/exercises/reorder",
        json={
            "items": [
                {"workout_exercise_id": str(exercise1_id), "order_index": 0}
                # Missing exercise2_id - should fail
            ]
        },
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "all exercises" in response.json()["detail"].lower()


def test_reorder_exercises_duplicate_order_index(client, db, test_user, test_exercise, auth_headers):
    """Test that duplicate order_index returns 400."""
    # Setup: workout with two exercises
    from app.models.exercise import ExerciseLibrary
    exercise2 = ExerciseLibrary(
        id=uuid4(),
        name="Squat",
        primary_muscle_group="legs",
        equipment="barbell",
        movement_type="compound",
        normalized_name="squat"
    )
    db.add(exercise2)
    db.commit()
    
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
    exercise1_id = response.json()["exercises"][0]["id"]
    
    response = client.post(
        f"/api/v1/workouts/{workout_id}/exercises",
        json={"exercise_id": str(exercise2.id)},
        headers=auth_headers
    )
    exercise2_id = response.json()["exercises"][1]["id"]
    
    # Try to reorder with duplicate order_index
    response = client.patch(
        f"/api/v1/workouts/{workout_id}/exercises/reorder",
        json={
            "items": [
                {"workout_exercise_id": str(exercise1_id), "order_index": 0},
                {"workout_exercise_id": str(exercise2_id), "order_index": 0}  # Duplicate!
            ]
        },
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "unique" in response.json()["detail"].lower() or "sequential" in response.json()["detail"].lower()
