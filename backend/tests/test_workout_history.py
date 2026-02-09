"""
Integration tests for workout history and detail endpoints.
"""
import pytest
from uuid import uuid4
from fastapi import status
from datetime import datetime, timezone, timedelta
from app.models.user import User
from app.models.exercise import ExerciseLibrary
from app.models.workout import Workout
from app.utils.enums import LifecycleStatus, CompletionStatus, SetType


def test_get_workout_history_empty(client, db, test_user, auth_headers):
    """Test getting history when user has no workouts."""
    response = client.get(
        "/api/v1/workouts",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["items"] == []
    assert data["next_cursor"] is None


def test_get_workout_history_includes_finalized(client, db, test_user, test_exercise, auth_headers):
    """Test that history includes finalized workouts with completed/partial."""
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
    
    # Get history
    response = client.get(
        "/api/v1/workouts",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verify workout in history
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == workout_id
    assert data["items"][0]["completion_status"] == CompletionStatus.COMPLETED.value
    assert data["items"][0]["exercise_count"] == 1
    assert data["items"][0]["set_count"] == 1


def test_get_workout_history_excludes_abandoned(client, db, test_user, test_exercise, auth_headers):
    """Test that history excludes abandoned workouts."""
    # Start workout
    response = client.post("/api/v1/workouts/start", headers=auth_headers)
    workout_id = response.json()["id"]
    
    # Abandon workout (manually set status)
    workout = db.query(Workout).filter(Workout.id == workout_id).first()
    workout.lifecycle_status = LifecycleStatus.ABANDONED.value
    workout.completion_status = None
    db.commit()
    
    # Get history
    response = client.get(
        "/api/v1/workouts",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verify abandoned workout NOT in history
    assert len(data["items"]) == 0


def test_get_workout_history_pagination(client, db, test_user, test_exercise, auth_headers):
    """Test pagination with cursor (including tie-breaker)."""
    from datetime import datetime, timezone, timedelta
    from app.models.workout import Workout
    
    # Set deterministic start_time values across multiple days
    # This ensures date ordering test is meaningful (not all workouts on same date)
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    
    # Create 25 finalized workouts
    workout_ids = []
    for i in range(25):
        response = client.post("/api/v1/workouts/start", headers=auth_headers)
        workout_id = response.json()["id"]
        
        # Set deterministic start_time across multiple days
        # Use days instead of minutes to guarantee different dates for ordering test
        workout = db.query(Workout).filter(Workout.id == workout_id).first()
        workout.start_time = base + timedelta(days=i)
        db.commit()
        
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
        
        response = client.post(
            f"/api/v1/workouts/{workout_id}/finish",
            json={"completion_status": CompletionStatus.COMPLETED.value},
            headers=auth_headers
        )
        workout_ids.append(workout_id)
    
    # Get first page (limit 20)
    response = client.get(
        "/api/v1/workouts?limit=20",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert len(data["items"]) == 20
    assert data["next_cursor"] is not None
    # Cursor format is now "timestamp|id" (e.g., "2026-01-25T10:30:00Z|uuid")
    assert "|" in data["next_cursor"]  # Verify cursor contains both timestamp and ID
    assert data["next_cursor"].split("|")[0].endswith("Z")  # Verify timestamp part ends with Z
    
    # Get next page using cursor
    response = client.get(
        f"/api/v1/workouts?cursor={data['next_cursor']}&limit=20",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data2 = response.json()
    
    assert len(data2["items"]) == 5  # Remaining 5 items
    assert data2["next_cursor"] is None  # No more items
    
    # Verify no duplicates between pages
    first_page_ids = {item["id"] for item in data["items"]}
    second_page_ids = {item["id"] for item in data2["items"]}
    assert len(first_page_ids & second_page_ids) == 0, "No duplicates between pages"
    
    # Pagination ordering check (ensures tie-breaker is correct)
    # Items should be descending by date (newest first)
    # Since we set start_time across multiple days (timedelta(days=i)), dates will be different
    items = data["items"]
    if len(items) > 1:
        # First item should have date >= last item (descending order)
        # With workouts across multiple days, this test is meaningful
        first_date = items[0]["date"]
        last_date = items[-1]["date"]
        assert first_date >= last_date, "Items should be in descending order (newest first)"


def test_get_workout_history_invalid_cursor(client, db, test_user, auth_headers):
    """Test that invalid cursor returns 400."""
    # Error messages are now consistent, so test can check for "Invalid cursor format" only
    # Test invalid timestamp format
    response = client.get(
        "/api/v1/workouts?cursor=invalid",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid cursor format" in response.json()["detail"]
    
    # Test invalid ID format in cursor
    response = client.get(
        "/api/v1/workouts?cursor=2026-01-25T10:30:00Z|invalid-uuid",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid cursor format" in response.json()["detail"]


def test_get_workout_history_legacy_cursor(client, db, test_user, test_exercise, auth_headers):
    """Test that legacy cursor (timestamp-only, no ID) still works."""
    from datetime import datetime, timezone, timedelta
    from app.models.workout import Workout
    
    # Create a few finalized workouts with deterministic start_time across multiple days
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    workout_ids = []
    
    for i in range(5):
        response = client.post("/api/v1/workouts/start", headers=auth_headers)
        workout_id = response.json()["id"]
        
        # Set start_time across multiple days for meaningful date ordering
        workout = db.query(Workout).filter(Workout.id == workout_id).first()
        workout.start_time = base + timedelta(days=i)
        db.commit()
        
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
        
        response = client.post(
            f"/api/v1/workouts/{workout_id}/finish",
            json={"completion_status": CompletionStatus.COMPLETED.value},
            headers=auth_headers
        )
        workout_ids.append(workout_id)
    
    # Get first page
    response = client.get(
        "/api/v1/workouts?limit=3",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert len(data["items"]) == 3
    assert data["next_cursor"] is not None
    
    # Test legacy cursor format (timestamp-only, no ID)
    # Extract timestamp part from cursor (remove ID)
    cursor_with_id = data["next_cursor"]
    assert "|" in cursor_with_id, "Cursor should contain ID"
    
    # Request with legacy cursor (timestamp-only)
    cursor_timestamp_only = cursor_with_id.split("|")[0]
    response = client.get(
        f"/api/v1/workouts?cursor={cursor_timestamp_only}&limit=20",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data2 = response.json()
    
    # Should still work (backward compatibility)
    assert len(data2["items"]) == 2  # Remaining 2 items


def test_get_workout_detail_success(client, db, test_user, test_exercise, auth_headers):
    """Test getting workout detail."""
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
    
    # Get detail
    response = client.get(
        f"/api/v1/workouts/{workout_id}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verify full workout returned
    assert data["id"] == workout_id
    assert data["lifecycle_status"] == LifecycleStatus.FINALIZED.value
    assert len(data["exercises"]) == 1
    assert len(data["exercises"][0]["sets"]) == 1


def test_get_workout_detail_wrong_user(client, db, test_user, test_exercise, auth_headers):
    """Test that cannot get detail for other user's workout."""
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
    
    # Create workout for other user (manually)
    from app.models.workout import Workout
    other_workout = Workout(
        id=uuid4(),
        user_id=other_user.id,
        lifecycle_status=LifecycleStatus.FINALIZED.value,
        completion_status=CompletionStatus.COMPLETED.value
    )
    db.add(other_workout)
    db.commit()
    
    # Try to get detail
    response = client.get(
        f"/api/v1/workouts/{other_workout.id}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
