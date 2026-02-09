"""
Unit tests for authentication utilities (password hashing and JWT).
"""
import pytest
from datetime import timedelta
from uuid import uuid4

from app.utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)


def test_hash_password():
    """Test password hashing."""
    password = "testpassword123"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_hash_password_different_salts():
    """Test that same password produces different hashes (different salts)."""
    password = "testpassword123"
    hashed1 = hash_password(password)
    hashed2 = hash_password(password)
    
    # Hashes should be different (different salts)
    assert hashed1 != hashed2
    
    # But both should verify correctly
    assert verify_password(password, hashed1) is True
    assert verify_password(password, hashed2) is True


def test_create_access_token():
    """Test JWT token creation."""
    user_id = uuid4()
    token = create_access_token(user_id)
    
    # Token should be a string
    assert isinstance(token, str)
    assert len(token) > 0
    
    # Should be able to decode it (returns tuple: (user_id, error_code))
    decoded_id, error_code = decode_access_token(token)
    assert decoded_id == user_id
    assert error_code is None


def test_token_expiration():
    """Test JWT token expiration."""
    user_id = uuid4()
    
    # Create expired token (expires in the past)
    expired_token = create_access_token(user_id, expires_delta=timedelta(seconds=-1))
    
    # Should return (None, "expired") for expired token
    decoded_id, error_code = decode_access_token(expired_token)
    assert decoded_id is None
    assert error_code == "expired"


def test_token_custom_expiration():
    """Test JWT token with custom expiration."""
    user_id = uuid4()
    
    # Create token with 1 hour expiration
    token = create_access_token(user_id, expires_delta=timedelta(hours=1))
    
    # Should decode successfully
    decoded_id, error_code = decode_access_token(token)
    assert decoded_id == user_id
    assert error_code is None


def test_decode_invalid_token():
    """Test decoding invalid token returns (None, "invalid")."""
    invalid_token = "invalid.jwt.token"
    decoded_id, error_code = decode_access_token(invalid_token)
    assert decoded_id is None
    assert error_code == "invalid"
