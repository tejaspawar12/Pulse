"""
Integration tests for error handling (401 Unauthorized).
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import timedelta

from app.models.user import User
from app.utils.auth import hash_password, create_access_token


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


def test_401_without_token(client: TestClient):
    """Test endpoints return 401 without token."""
    response = client.get("/api/v1/workouts/active")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_401_invalid_token(client: TestClient):
    """Test endpoints return 401 with invalid token."""
    response = client.get(
        "/api/v1/workouts/active",
        headers={"Authorization": "Bearer invalid-token"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_401_expired_token(client: TestClient, db: Session, test_user: User):
    """Test endpoints return 401 with expired token."""
    # Create expired token (expires in the past)
    expired_token = create_access_token(
        test_user.id,
        expires_delta=timedelta(seconds=-1)
    )
    
    response = client.get(
        "/api/v1/workouts/active",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_401_without_token_on_protected_endpoints(client: TestClient):
    """Test all protected endpoints return 401 without token."""
    endpoints = [
        ("GET", "/api/v1/workouts/active"),
        ("POST", "/api/v1/workouts/start"),
        ("GET", "/api/v1/workouts/history"),
        ("GET", "/api/v1/users/me"),
        ("PATCH", "/api/v1/users/me"),
    ]
    
    for method, endpoint in endpoints:
        if method == "GET":
            response = client.get(endpoint)
        elif method == "POST":
            response = client.post(endpoint)
        elif method == "PATCH":
            response = client.patch(endpoint, json={})
        else:
            continue
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
            f"{method} {endpoint} should return 401 without token"
