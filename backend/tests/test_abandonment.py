"""
Integration tests for workout abandonment logic.
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from freezegun import freeze_time  # ✅ Required for time-based tests

from app.models.user import User
from app.models.workout import Workout, LifecycleStatus
from app.utils.auth import hash_password, create_access_token
from app.config.settings import settings


def get_auth_token(client: TestClient, user: User) -> str:
    """Helper to get auth token for a user."""
    token = create_access_token(user.id)
    return token


@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user."""
    user = User(
        id=uuid4(),
        email="testuser@example.com",
        password_hash=hash_password("testpassword123"),
        units="kg",
        timezone="Asia/Kolkata",
        default_rest_timer_seconds=90
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_auto_abandon_old_draft(client: TestClient, db: Session, test_user: User):
    """Test that draft workout >= 24h old is auto-abandoned."""
    from freezegun import freeze_time
    
    token = get_auth_token(client, test_user)
    
    # ✅ Freeze time for deterministic test
    frozen_time = datetime.now(timezone.utc)
    old_start_time = frozen_time - timedelta(hours=25)
    
    # Create a draft workout with start_time > 24h ago
    old_workout = Workout(
        id=uuid4(),
        user_id=test_user.id,
        lifecycle_status=LifecycleStatus.DRAFT.value,
        start_time=old_start_time
    )
    db.add(old_workout)
    db.commit()
    db.refresh(old_workout)
    
    # ✅ Freeze time when checking (ensures deterministic age calculation)
    with freeze_time(frozen_time):
        # Call get_active_workout - should auto-abandon
        response = client.get(
            "/api/v1/workouts/active",
            headers={"Authorization": f"Bearer {token}"}
        )
    
    # Should return None (no active workout)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() is None
    
    # Verify workout is abandoned
    db.refresh(old_workout)
    assert old_workout.lifecycle_status == LifecycleStatus.ABANDONED.value
    assert old_workout.completion_status is None


def test_abandoned_not_in_history(client: TestClient, db: Session, test_user: User):
    """Test that abandoned workouts are excluded from history."""
    from freezegun import freeze_time
    
    token = get_auth_token(client, test_user)
    
    # ✅ Freeze time for deterministic test
    frozen_time = datetime.now(timezone.utc)
    
    # Create abandoned workout
    abandoned_workout = Workout(
        id=uuid4(),
        user_id=test_user.id,
        lifecycle_status=LifecycleStatus.ABANDONED.value,
        completion_status=None,
        start_time=frozen_time - timedelta(hours=25)
    )
    db.add(abandoned_workout)
    db.commit()
    
    # Create finalized workout (should be in history)
    # History requires finalized workouts with end_time
    finalized_start = frozen_time - timedelta(days=1)
    finalized_workout = Workout(
        id=uuid4(),
        user_id=test_user.id,
        lifecycle_status=LifecycleStatus.FINALIZED.value,
        completion_status="completed",
        start_time=finalized_start,
        end_time=finalized_start + timedelta(minutes=60)  # Add end_time for finalized workout
    )
    db.add(finalized_workout)
    db.commit()
    
    # Get history (endpoint is /api/v1/workouts, not /api/v1/workouts/history)
    response = client.get(
        "/api/v1/workouts",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK, f"Expected 200, got {response.status_code}: {response.json() if response.status_code < 500 else response.text}"
    history_data = response.json()
    # History returns WorkoutHistoryOut with 'items' field
    history = history_data.get("items", [])
    
    # Verify abandoned workout NOT in history
    workout_ids = [w["id"] for w in history]
    assert str(abandoned_workout.id) not in workout_ids
    
    # Verify finalized workout IS in history
    assert str(finalized_workout.id) in workout_ids


def test_abandoned_no_daily_state(client: TestClient, db: Session, test_user: User):
    """Test that abandoned workouts do NOT write to daily_training_state."""
    from app.models.daily_training_state import DailyTrainingState
    from freezegun import freeze_time
    
    token = get_auth_token(client, test_user)
    
    # ✅ Freeze time for deterministic test
    frozen_time = datetime.now(timezone.utc)
    
    # Count initial daily_training_state entries
    initial_count = db.query(DailyTrainingState).filter(
        DailyTrainingState.user_id == test_user.id
    ).count()
    
    # Create abandoned workout
    abandoned_workout = Workout(
        id=uuid4(),
        user_id=test_user.id,
        lifecycle_status=LifecycleStatus.ABANDONED.value,
        completion_status=None,
        start_time=frozen_time - timedelta(hours=25)
    )
    db.add(abandoned_workout)
    db.commit()
    
    # ✅ Trigger auto-abandon with frozen time
    with freeze_time(frozen_time):
        response = client.get(
            "/api/v1/workouts/active",
            headers={"Authorization": f"Bearer {token}"}
        )
    
    # Verify no new daily_training_state entry
    final_count = db.query(DailyTrainingState).filter(
        DailyTrainingState.user_id == test_user.id
    ).count()
    
    assert final_count == initial_count, "Abandoned workout should NOT create daily_training_state entry"


def test_abandon_exactly_24h_abandoned(client: TestClient, db: Session, test_user: User):
    """Test that workout exactly 24h old is abandoned (>= 24h boundary)."""
    from freezegun import freeze_time
    
    # Verify constant value
    assert settings.ABANDON_AFTER_HOURS == 24
    
    token = get_auth_token(client, test_user)
    
    # ✅ Freeze time at a specific point
    frozen_time = datetime.now(timezone.utc)
    exactly_24h_ago = frozen_time - timedelta(hours=24)
    
    # Create draft workout exactly 24h old
    workout_24h = Workout(
        id=uuid4(),
        user_id=test_user.id,
        lifecycle_status=LifecycleStatus.DRAFT.value,
        start_time=exactly_24h_ago
    )
    db.add(workout_24h)
    db.commit()
    
    # ✅ Freeze time at exactly 24h after start
    # ⚠️ IMPORTANT: If abandonment logic uses SQL now(), freezegun won't freeze DB time.
    # Must use Python datetime.now(timezone.utc) for age checks, or accept injected now().
    with freeze_time(frozen_time):
        response = client.get(
            "/api/v1/workouts/active",
            headers={"Authorization": f"Bearer {token}"}
        )
    
    # ✅ Exactly 24h should be abandoned (>= 24h rule)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() is None  # No active workout (abandoned)
    
    # Verify workout is abandoned
    db.refresh(workout_24h)
    assert workout_24h.lifecycle_status == LifecycleStatus.ABANDONED.value
    assert workout_24h.completion_status is None


def test_abandon_just_under_24h_not_abandoned(client: TestClient, db: Session, test_user: User):
    """Test that workout just under 24h old is NOT abandoned (< 24h boundary)."""
    from freezegun import freeze_time
    
    token = get_auth_token(client, test_user)
    
    # ✅ Freeze time at a specific point
    frozen_time = datetime.now(timezone.utc)
    just_under_24h_ago = frozen_time - timedelta(hours=23, minutes=59)
    
    # Create draft workout just under 24h old
    workout_23h = Workout(
        id=uuid4(),
        user_id=test_user.id,
        lifecycle_status=LifecycleStatus.DRAFT.value,
        start_time=just_under_24h_ago
    )
    db.add(workout_23h)
    db.commit()
    
    # ✅ Freeze time when checking
    # ⚠️ IMPORTANT: If abandonment logic uses SQL now(), freezegun won't freeze DB time.
    # Must use Python datetime.now(timezone.utc) for age checks, or accept injected now().
    with freeze_time(frozen_time):
        response = client.get(
            "/api/v1/workouts/active",
            headers={"Authorization": f"Bearer {token}"}
        )
    
    # Should still be active (< 24h)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() is not None
    assert response.json()["id"] == str(workout_23h.id)
    
    # Verify workout is still draft (not abandoned)
    db.refresh(workout_23h)
    assert workout_23h.lifecycle_status == LifecycleStatus.DRAFT.value


def test_start_workout_abandons_old_draft(client: TestClient, db: Session, test_user: User):
    """Test that start_workout abandons old draft (>= 24h) before creating new one."""
    from freezegun import freeze_time
    
    token = get_auth_token(client, test_user)
    
    # ✅ Freeze time for deterministic test
    frozen_time = datetime.now(timezone.utc)
    old_start_time = frozen_time - timedelta(hours=25)
    
    # Create old draft (>= 24h old)
    old_workout = Workout(
        id=uuid4(),
        user_id=test_user.id,
        lifecycle_status=LifecycleStatus.DRAFT.value,
        start_time=old_start_time
    )
    db.add(old_workout)
    db.commit()
    old_workout_id = old_workout.id
    
    # ✅ Freeze time when starting new workout
    with freeze_time(frozen_time):
        # Start new workout (should abandon old one)
        response = client.post(
            "/api/v1/workouts/start",
            headers={"Authorization": f"Bearer {token}"}
        )
    
    assert response.status_code == status.HTTP_200_OK
    new_workout_id = response.json()["id"]
    
    # Verify old workout is abandoned
    db.refresh(old_workout)
    assert old_workout.lifecycle_status == LifecycleStatus.ABANDONED.value
    assert old_workout.completion_status is None
    
    # Verify new workout is created (different ID)
    assert new_workout_id != str(old_workout_id)
