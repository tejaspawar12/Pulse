"""
Integration tests for data isolation (multi-user security).
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from app.models.user import User
from app.models.workout import Workout, LifecycleStatus
from app.utils.auth import hash_password, create_access_token


def get_auth_token(client: TestClient, user: User) -> str:
    """Helper to get auth token for a user."""
    token = create_access_token(user.id)
    return token


@pytest.fixture
def user_a(db: Session) -> User:
    """Create User A."""
    user = User(
        id=uuid4(),
        email="usera@example.com",
        password_hash=hash_password("password"),
        units="kg",
        timezone="Asia/Kolkata"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def user_b(db: Session) -> User:
    """Create User B."""
    user = User(
        id=uuid4(),
        email="userb@example.com",
        password_hash=hash_password("password"),
        units="kg",
        timezone="America/New_York"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_user_cannot_see_other_workouts(client: TestClient, db: Session, user_a: User, user_b: User):
    """Test User A cannot see User B's workouts."""
    token_a = get_auth_token(client, user_a)
    token_b = get_auth_token(client, user_b)
    
    # User B creates workout
    response = client.post(
        "/api/v1/workouts/start",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    workout_b_id = response.json()["id"]
    
    # User A tries to get User B's workout
    response = client.get(
        f"/api/v1/workouts/{workout_b_id}",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    
    # ✅ Prefer 404 (don't leak existence) but 403 is also acceptable
    assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN]


def test_user_cannot_modify_other_workouts(client: TestClient, db: Session, user_a: User, user_b: User):
    """Test User A cannot modify User B's workouts."""
    token_a = get_auth_token(client, user_a)
    token_b = get_auth_token(client, user_b)
    
    # User B creates workout
    response = client.post(
        "/api/v1/workouts/start",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    workout_b_id = response.json()["id"]
    
    # User A tries to finish User B's workout
    response = client.post(
        f"/api/v1/workouts/{workout_b_id}/finish",
        json={"completion_status": "completed"},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    
    # ✅ Prefer 404 (don't leak existence) but 403 is also acceptable
    assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN]


def test_user_cannot_see_other_history(client: TestClient, db: Session, user_a: User, user_b: User):
    """Test User A's history doesn't include User B's workouts."""
    token_a = get_auth_token(client, user_a)
    token_b = get_auth_token(client, user_b)
    
    # User B creates and finishes workout
    response = client.post(
        "/api/v1/workouts/start",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    workout_b_id = response.json()["id"]
    response = client.post(
        f"/api/v1/workouts/{workout_b_id}/finish",
        json={"completion_status": "completed"},
        headers={"Authorization": f"Bearer {token_b}"}
    )
    
    # User A gets history
    response = client.get(
        "/api/v1/workouts/history",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    
    history_data = response.json()
    # History returns WorkoutHistoryOut with 'items' field
    history = history_data.get("items", [])
    workout_ids = [w["id"] for w in history]
    
    # User B's workout should NOT be in User A's history
    assert str(workout_b_id) not in workout_ids


def test_user_cannot_update_other_settings(client: TestClient, db: Session, user_a: User, user_b: User):
    """Test User A cannot update User B's settings."""
    token_a = get_auth_token(client, user_a)
    
    # User A tries to update settings (should only update their own)
    response = client.patch(
        "/api/v1/users/me",
        json={"units": "lb"},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    
    # Should succeed (updates User A's own settings)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["units"] == "lb"
    
    # Verify User B's settings unchanged
    db.refresh(user_b)
    assert user_b.units == "kg"  # User B's original units
