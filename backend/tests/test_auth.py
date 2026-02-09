"""
Integration tests for authentication endpoints.
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from app.models.user import User
from app.utils.auth import hash_password, create_access_token
from datetime import timedelta


def test_register_success(client: TestClient, db: Session):
    """Test successful user registration."""
    data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "timezone": "America/New_York"
    }
    response = client.post("/api/v1/auth/register", json=data)
    
    assert response.status_code == status.HTTP_201_CREATED
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"
    assert "expires_in" in response.json()
    assert response.json()["user"]["email"] == "test@example.com"
    assert "password_hash" not in response.json()["user"]  # Never return password_hash
    
    # Verify user was created in database
    user = db.query(User).filter(User.email == "test@example.com").first()
    assert user is not None
    assert user.timezone == "America/New_York"


def test_register_duplicate_email(client: TestClient, db: Session):
    """Test registration with duplicate email returns 409."""
    # Create test user first
    existing_user = User(
        id=uuid4(),
        email="existing@example.com",
        password_hash=hash_password("testpassword123"),
        units="kg",
        timezone="Asia/Kolkata",
        default_rest_timer_seconds=90
    )
    db.add(existing_user)
    db.commit()
    db.refresh(existing_user)
    
    # Try to register with same email
    data = {
        "email": existing_user.email,
        "password": "testpassword123"
    }
    response = client.post("/api/v1/auth/register", json=data)
    
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "already registered" in response.json()["detail"].lower()


def test_register_invalid_email(client: TestClient, db: Session):
    """Test registration with invalid email returns 422."""
    data = {
        "email": "not-an-email",
        "password": "testpassword123"
    }
    response = client.post("/api/v1/auth/register", json=data)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_register_short_password(client: TestClient, db: Session):
    """Test registration with short password returns 422."""
    data = {
        "email": "test@example.com",
        "password": "short"  # Less than 8 characters
    }
    response = client.post("/api/v1/auth/register", json=data)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_register_invalid_timezone(client: TestClient, db: Session):
    """Test registration with invalid timezone returns 422 (validation error)."""
    data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "timezone": "Invalid/Timezone"
    }
    response = client.post("/api/v1/auth/register", json=data)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Pydantic validation errors may be in different format, check for timezone error
    detail = response.json().get("detail", [])
    if isinstance(detail, list):
        # Pydantic v2 format - list of errors
        error_messages = " ".join([str(err.get("msg", "")) for err in detail])
        assert "timezone" in error_messages.lower() or "invalid" in error_messages.lower()
    else:
        # String format
        assert "timezone" in str(detail).lower() or "invalid" in str(detail).lower()


def test_register_email_normalization(client: TestClient, db: Session):
    """Test that email is normalized (lowercase + strip)."""
    data = {
        "email": "  Test@Example.COM  ",  # Has spaces and mixed case
        "password": "testpassword123"
    }
    response = client.post("/api/v1/auth/register", json=data)
    
    assert response.status_code == status.HTTP_201_CREATED
    # Email should be normalized in response
    assert response.json()["user"]["email"] == "test@example.com"
    
    # Verify normalized email in database
    user = db.query(User).filter(User.email == "test@example.com").first()
    assert user is not None


def test_login_success(client: TestClient, db: Session):
    """Test successful login."""
    # Create test user with known password
    test_password = "testpassword123"
    test_user = User(
        id=uuid4(),
        email="test@example.com",
        password_hash=hash_password(test_password),  # Explicitly hash password
        units="kg",
        timezone="Asia/Kolkata",
        default_rest_timer_seconds=90
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    
    data = {
        "email": test_user.email,
        "password": test_password
    }
    response = client.post("/api/v1/auth/login", json=data)
    
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"
    assert "expires_in" in response.json()
    assert response.json()["user"]["email"] == test_user.email


def test_login_wrong_password(client: TestClient, db: Session):
    """Test login with wrong password returns 401."""
    # Create test user with known password
    test_user = User(
        id=uuid4(),
        email="test@example.com",
        password_hash=hash_password("testpassword123"),  # Explicitly hash password
        units="kg",
        timezone="Asia/Kolkata",
        default_rest_timer_seconds=90
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    
    data = {
        "email": test_user.email,
        "password": "wrongpassword"
    }
    response = client.post("/api/v1/auth/login", json=data)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "invalid" in response.json()["detail"].lower()


def test_login_nonexistent_email(client: TestClient, db: Session):
    """Test login with non-existent email returns 401."""
    data = {
        "email": "nonexistent@example.com",
        "password": "testpassword123"
    }
    response = client.post("/api/v1/auth/login", json=data)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    # Should not reveal if email exists (security best practice)
    assert "invalid" in response.json()["detail"].lower()


def test_login_email_normalization(client: TestClient, db: Session):
    """Test that login normalizes email (lowercase + strip)."""
    test_password = "testpassword123"
    test_user = User(
        id=uuid4(),
        email="test@example.com",
        password_hash=hash_password(test_password),
        units="kg",
        timezone="Asia/Kolkata",
        default_rest_timer_seconds=90
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    
    # Try login with mixed case and spaces
    data = {
        "email": "  Test@Example.COM  ",
        "password": test_password
    }
    response = client.post("/api/v1/auth/login", json=data)
    
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()


def test_jwt_token_valid(client: TestClient, db: Session):
    """Test using valid JWT token to access protected endpoint."""
    # Create test user with known password
    test_password = "testpassword123"
    test_user = User(
        id=uuid4(),
        email="test@example.com",
        password_hash=hash_password(test_password),  # Explicitly hash password
        units="kg",
        timezone="Asia/Kolkata",
        default_rest_timer_seconds=90
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    
    # Login to get token
    login_data = {
        "email": test_user.email,
        "password": test_password
    }
    login_response = client.post("/api/v1/auth/login", json=login_data)
    token = login_response.json()["access_token"]
    
    # Use token to access protected endpoint
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"] == test_user.email


def test_jwt_token_missing(client: TestClient):
    """Test missing JWT token returns 401."""
    response = client.get("/api/v1/users/me")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "authentication required" in response.json()["detail"].lower()


def test_jwt_token_invalid(client: TestClient):
    """Test invalid JWT token returns 401."""
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid-token"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "invalid" in response.json()["detail"].lower()


def test_jwt_token_expired(client: TestClient, db: Session):
    """Test expired JWT token returns 401 with 'expired' message."""
    # Create test user
    test_user = User(
        id=uuid4(),
        email="test@example.com",
        password_hash=hash_password("testpassword123"),
        units="kg",
        timezone="Asia/Kolkata",
        default_rest_timer_seconds=90
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    
    # Create expired token (expires 1 second ago)
    expired_token = create_access_token(
        test_user.id,
        expires_delta=timedelta(seconds=-1)  # Expired token
    )
    
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "expired" in response.json()["detail"].lower()  # Should specifically say "expired"
