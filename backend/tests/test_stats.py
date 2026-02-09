"""
Integration tests for stats endpoints: summary, streak, volume.
Phase 2 Week 3 Day 5.
"""
import pytest
from uuid import uuid4
from fastapi import status
from datetime import datetime, timezone, timedelta

from app.models.user import User
from app.models.exercise import ExerciseLibrary
from app.models.workout import Workout, WorkoutExercise, WorkoutSet
from app.utils.enums import LifecycleStatus, CompletionStatus, SetType


def test_get_summary_returns_200_and_shape(client, db, test_user, test_exercise, auth_headers):
    """GET /users/me/stats/summary?days=30 returns 200 and correct shape."""
    response = client.get(
        "/api/v1/users/me/stats/summary",
        params={"days": 30},
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "period_days" in data
    assert data["period_days"] == 30
    assert "total_workouts" in data
    assert "total_volume_kg" in data
    assert "total_sets" in data
    assert "prs_hit" in data
    assert "avg_workout_duration_minutes" in data
    assert "most_trained_muscle" in data


def test_get_summary_no_workouts_returns_zeros(client, auth_headers):
    """With no workouts, summary totals are 0."""
    response = client.get(
        "/api/v1/users/me/stats/summary",
        params={"days": 30},
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_workouts"] == 0
    assert data["total_volume_kg"] == 0.0
    assert data["total_sets"] == 0
    assert data["prs_hit"] == 0
    assert data["avg_workout_duration_minutes"] is None
    assert data["most_trained_muscle"] is None


def test_get_summary_with_workouts(client, db, test_user, test_exercise, auth_headers):
    """With finalized workouts in period, summary reflects data."""
    # test_user has timezone UTC; create workout "yesterday" in UTC
    start = datetime.now(timezone.utc) - timedelta(days=1)
    end = start + timedelta(hours=1)
    workout = Workout(
        id=uuid4(),
        user_id=test_user.id,
        start_time=start,
        end_time=end,
        lifecycle_status=LifecycleStatus.FINALIZED.value,
        completion_status=CompletionStatus.COMPLETED.value,
        duration_minutes=60,
    )
    db.add(workout)
    db.flush()

    we = WorkoutExercise(
        id=uuid4(),
        workout_id=workout.id,
        exercise_id=test_exercise.id,
        order_index=0,
    )
    db.add(we)
    db.flush()

    ws = WorkoutSet(
        id=uuid4(),
        workout_exercise_id=we.id,
        set_number=1,
        reps=10,
        weight=100.0,
        set_type=SetType.WORKING.value,
    )
    db.add(ws)
    db.commit()

    response = client.get(
        "/api/v1/users/me/stats/summary",
        params={"days": 30},
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_workouts"] == 1
    assert data["total_volume_kg"] == 1000.0  # 100 * 10
    assert data["total_sets"] == 1
    assert data["avg_workout_duration_minutes"] == 60
    assert data["most_trained_muscle"] == "chest"


def test_get_streak_returns_200(client, auth_headers):
    """GET /users/me/stats/streak returns 200."""
    response = client.get(
        "/api/v1/users/me/stats/streak",
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "current_streak_days" in data
    assert "longest_streak_days" in data
    assert "last_workout_date" in data


def test_get_streak_no_workouts_returns_zeros_and_null(client, auth_headers):
    """With no workouts, streak is 0 and last_workout_date null."""
    response = client.get(
        "/api/v1/users/me/stats/streak",
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["current_streak_days"] == 0
    assert data["longest_streak_days"] == 0
    assert data["last_workout_date"] is None


def test_get_volume_returns_200_and_list(client, auth_headers):
    """GET /users/me/stats/volume?days=30&group_by=week returns 200 and list of buckets."""
    response = client.get(
        "/api/v1/users/me/stats/volume",
        params={"days": 30, "group_by": "week"},
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "period_days" in data
    assert data["period_days"] == 30
    assert isinstance(data["data"], list)


def test_get_volume_group_by_day(client, auth_headers):
    """GET /users/me/stats/volume?days=7&group_by=day returns 200."""
    response = client.get(
        "/api/v1/users/me/stats/volume",
        params={"days": 7, "group_by": "day"},
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert data["period_days"] == 7


def test_stats_unauthenticated_returns_401(client):
    """Stats endpoints return 401 without auth."""
    r1 = client.get("/api/v1/users/me/stats/summary", params={"days": 30})
    r2 = client.get("/api/v1/users/me/stats/streak")
    r3 = client.get("/api/v1/users/me/stats/volume", params={"days": 30, "group_by": "week"})
    assert r1.status_code == status.HTTP_401_UNAUTHORIZED
    assert r2.status_code == status.HTTP_401_UNAUTHORIZED
    assert r3.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_summary_invalid_days_returns_422(client, auth_headers):
    """Invalid days (e.g. 0 or 400) returns 422."""
    r1 = client.get(
        "/api/v1/users/me/stats/summary",
        params={"days": 0},
        headers=auth_headers,
    )
    r2 = client.get(
        "/api/v1/users/me/stats/summary",
        params={"days": 400},
        headers=auth_headers,
    )
    assert r1.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert r2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_volume_invalid_group_by_returns_422(client, auth_headers):
    """Invalid group_by returns 422."""
    response = client.get(
        "/api/v1/users/me/stats/volume",
        params={"days": 30, "group_by": "month"},
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
