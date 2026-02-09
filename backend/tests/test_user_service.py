"""
Unit tests for UserService.
"""
import pytest
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from uuid import uuid4

from app.models.user import User
from app.services.user_service import UserService
from app.schemas.user import UpdateUserIn, Units
from app.utils.auth import hash_password


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


def test_update_user_settings(db: Session, test_user: User):
    """Test updating user settings."""
    service = UserService(db)
    
    # Update units
    updated = service.update_user_settings(
        test_user.id,
        UpdateUserIn(units=Units.lb)
    )
    
    assert updated.units == "lb"
    
    # Update timezone
    updated = service.update_user_settings(
        test_user.id,
        UpdateUserIn(timezone="America/New_York")
    )
    
    assert updated.timezone == "America/New_York"
    
    # Update rest timer
    updated = service.update_user_settings(
        test_user.id,
        UpdateUserIn(default_rest_timer_seconds=120)
    )
    
    assert updated.default_rest_timer_seconds == 120


def test_update_invalid_timezone(db: Session, test_user: User):
    """Test updating with invalid timezone."""
    service = UserService(db)
    
    with pytest.raises(HTTPException) as exc:
        service.update_user_settings(
            test_user.id,
            UpdateUserIn(timezone="Invalid/Timezone")
        )
    
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid timezone" in exc.value.detail


def test_update_user_not_found(db: Session):
    """Test updating non-existent user returns 404."""
    service = UserService(db)
    fake_user_id = uuid4()
    
    with pytest.raises(HTTPException) as exc:
        service.update_user_settings(
            fake_user_id,
            UpdateUserIn(units=Units.lb)
        )
    
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in exc.value.detail.lower()


def test_update_partial_settings(db: Session, test_user: User):
    """Test updating only some settings (others remain unchanged)."""
    service = UserService(db)
    
    original_timezone = test_user.timezone
    original_rest_timer = test_user.default_rest_timer_seconds
    
    # Update only units
    updated = service.update_user_settings(
        test_user.id,
        UpdateUserIn(units=Units.lb)
    )
    
    assert updated.units == "lb"
    assert updated.timezone == original_timezone
    assert updated.default_rest_timer_seconds == original_rest_timer
