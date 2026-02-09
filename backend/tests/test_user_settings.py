"""
Integration tests for user settings endpoints.
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from app.models.user import User
from app.utils.auth import hash_password, create_access_token


def get_auth_token(client: TestClient, user: User) -> str:
    """Helper to get auth token for a user."""
    # Create a token for the user
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


def test_update_units(client: TestClient, db: Session, test_user: User):
    """Test updating units."""
    token = get_auth_token(client, test_user)
    
    response = client.patch(
        "/api/v1/users/me",
        json={"units": "lb"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["units"] == "lb"
    
    # Verify in database
    db.refresh(test_user)
    assert test_user.units == "lb"


def test_update_timezone(client: TestClient, db: Session, test_user: User):
    """Test updating timezone."""
    token = get_auth_token(client, test_user)
    
    response = client.patch(
        "/api/v1/users/me",
        json={"timezone": "America/New_York"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["timezone"] == "America/New_York"
    
    # Verify in database
    db.refresh(test_user)
    assert test_user.timezone == "America/New_York"


def test_update_rest_timer(client: TestClient, db: Session, test_user: User):
    """Test updating rest timer."""
    token = get_auth_token(client, test_user)
    
    response = client.patch(
        "/api/v1/users/me",
        json={"default_rest_timer_seconds": 120},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["default_rest_timer_seconds"] == 120
    
    # Verify in database
    db.refresh(test_user)
    assert test_user.default_rest_timer_seconds == 120


def test_update_invalid_units(client: TestClient, db: Session, test_user: User):
    """Test updating with invalid units returns 422 (schema validation)."""
    token = get_auth_token(client, test_user)
    
    response = client.patch(
        "/api/v1/users/me",
        json={"units": "invalid"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # ✅ Units is an Enum in schema, so FastAPI/Pydantic rejects it before service runs → 422
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_update_invalid_timezone(client: TestClient, db: Session, test_user: User):
    """Test updating with invalid timezone returns 400 (service validation)."""
    token = get_auth_token(client, test_user)
    
    response = client.patch(
        "/api/v1/users/me",
        json={"timezone": "Invalid/Timezone"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # ✅ Still 400: Timezone validation is in service (business rule), not schema
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid timezone" in response.json()["detail"]


def test_update_negative_rest_timer(client: TestClient, db: Session, test_user: User):
    """Test updating with negative rest timer returns 422 (schema ge=0 validation)."""
    token = get_auth_token(client, test_user)
    
    response = client.patch(
        "/api/v1/users/me",
        json={"default_rest_timer_seconds": -1},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # ✅ Changed: Schema ge=0 validation returns 422, not 400
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_update_requires_auth(client: TestClient, db: Session):
    """Test updating settings requires authentication."""
    response = client.patch(
        "/api/v1/users/me",
        json={"units": "lb"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_partial(client: TestClient, db: Session, test_user: User):
    """Test updating only one field (partial update)."""
    token = get_auth_token(client, test_user)
    original_timezone = test_user.timezone
    original_rest_timer = test_user.default_rest_timer_seconds
    
    # Update only units
    response = client.patch(
        "/api/v1/users/me",
        json={"units": "lb"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["units"] == "lb"
    
    # Verify other fields unchanged
    db.refresh(test_user)
    assert test_user.units == "lb"
    assert test_user.timezone == original_timezone
    assert test_user.default_rest_timer_seconds == original_rest_timer
