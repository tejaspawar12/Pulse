"""
Authentication utilities: JWT token generation and password hashing.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from jose import JWTError, jwt, ExpiredSignatureError
import bcrypt
from app.config.settings import settings
from uuid import UUID

# Bcrypt configuration
BCRYPT_ROUNDS = 12  # Explicit 12 rounds (good balance of security and performance)

def hash_password(password: str) -> str:
    """
    Hash password using bcrypt.
    
    Args:
        password: Plain text password
    
    Returns:
        str: Hashed password (bcrypt hash string)
    """
    # Convert password to bytes
    password_bytes = password.encode('utf-8')
    # Generate salt and hash password
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)
    # Return as string (bcrypt hash is ASCII-safe)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password from database
    
    Returns:
        bool: True if password matches
    """
    # Convert to bytes
    password_bytes = plain_password.encode('utf-8')
    hash_bytes = hashed_password.encode('utf-8')
    # Verify password
    return bcrypt.checkpw(password_bytes, hash_bytes)

def create_access_token(user_id: UUID, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.
    
    Args:
        user_id: User UUID
        expires_delta: Optional expiration delta (defaults to JWT_EXPIRATION_DAYS)
    
    Returns:
        str: JWT token
    """
    # ⚠️ CRITICAL: Use timezone-aware datetime (best practice)
    now = datetime.now(timezone.utc)
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.JWT_EXPIRATION_DAYS)
    
    to_encode = {
        "sub": str(user_id),  # Standard JWT claim for subject (user ID)
        "exp": expire,
        "iat": now,  # Issued at
        "iss": settings.JWT_ISSUER,  # Issuer (prevents token confusion if multiple services)
        "aud": settings.JWT_AUDIENCE,  # Audience (prevents token confusion if multiple clients)
        # ⏳ Phase 2: Add "ver": 1 for token versioning (allows force logout, secret rotation)
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt

def decode_access_token(token: str) -> Tuple[Optional[UUID], Optional[str]]:
    """
    Decode JWT token and extract user ID.
    
    Args:
        token: JWT token string
    
    Returns:
        Tuple of (user_id, error_code):
        - (UUID, None) if token is valid
        - (None, "expired") if token is expired
        - (None, "invalid") if token is invalid (malformed, wrong signature, etc.)
    
    Note: Distinguishing expired vs invalid helps with better error messages and UX.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,  # Validate audience
            issuer=settings.JWT_ISSUER,  # Validate issuer
        )
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            return None, "invalid"
        return UUID(user_id_str), None
    except ExpiredSignatureError:
        return None, "expired"
    except JWTError:
        return None, "invalid"
