"""
Authentication service for user registration, login, and refresh tokens.
"""
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import LoginIn, RegisterIn
from app.utils.auth import create_access_token, hash_password, verify_password

# Refresh token configuration
REFRESH_TOKEN_EXPIRE_DAYS = 30
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Used when creating short-lived access tokens from refresh


def hash_token(token: str) -> str:
    """Hash token using SHA-256 (with optional pepper from settings)."""
    pepper = getattr(settings, "REFRESH_TOKEN_PEPPER", "") or ""
    return hashlib.sha256((token + pepper).encode()).hexdigest()


def create_refresh_token(
    user_id: uuid.UUID,
    db: Session,
    family_id: uuid.UUID | None = None,
    device_info: str | None = None,
    ip_hash: str | None = None,
) -> Tuple[RefreshToken, str]:
    """
    Create a new refresh token.

    Returns:
        Tuple of (RefreshToken model, raw_token string)
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash_val = hash_token(raw_token)

    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash_val,
        expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        token_family_id=family_id or uuid.uuid4(),
        device_info=device_info,
        ip_hash=ip_hash,
    )

    db.add(refresh_token)
    db.flush()

    return refresh_token, raw_token


def refresh_access_token(refresh_token: str, db: Session) -> dict:
    """
    Validate refresh token and issue new tokens.
    Implements token rotation with reuse detection.
    Uses SELECT FOR UPDATE to prevent race conditions.
    """
    token_hash_val = hash_token(refresh_token)

    stored_token = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash_val)
        .with_for_update()
        .first()
    )

    if not stored_token:
        raise ValueError("Token not found")

    # Check reuse (used_at set) before revoked_at so we raise "reuse detected" on second use
    if stored_token.used_at is not None:
        db.query(RefreshToken).filter(
            RefreshToken.token_family_id == stored_token.token_family_id
        ).update({"revoked_at": datetime.now(timezone.utc)})
        db.commit()
        raise ValueError("Token reuse detected - all sessions revoked")

    if stored_token.revoked_at:
        raise ValueError("Token revoked")

    if stored_token.expires_at < datetime.now(timezone.utc):
        raise ValueError("Token expired")

    stored_token.used_at = datetime.now(timezone.utc)
    db.flush()

    new_token, raw_token = create_refresh_token(
        user_id=stored_token.user_id,
        db=db,
        family_id=stored_token.token_family_id,
    )

    stored_token.revoked_at = datetime.now(timezone.utc)
    stored_token.replaced_by_id = new_token.id

    db.commit()

    user = db.get(User, stored_token.user_id)
    return {
        "access_token": create_access_token(user.id),
        "refresh_token": raw_token,
        "token_type": "bearer",
    }


def revoke_refresh_token(raw_refresh_token: str, db: Session) -> bool:
    """Revoke a single refresh token (by raw token string)."""
    token_hash_val = hash_token(raw_refresh_token)
    token = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash_val).first()

    if not token:
        return False

    token.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return True


def revoke_all_user_tokens(user_id: uuid.UUID, db: Session) -> int:
    """Revoke all refresh tokens for a user (logout all sessions)."""
    result = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
        .update({"revoked_at": datetime.now(timezone.utc)})
    )
    db.commit()
    return result


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, data: RegisterIn) -> Tuple[User, str]:
        """
        Register new user.
        
        Args:
            data: Registration data (email, password, optional timezone)
        
        Returns:
            Tuple of (User, JWT token)
        
        Raises:
            HTTPException: If email already exists or timezone invalid
        """
        # ⚠️ CRITICAL: Normalize email (lowercase + strip to avoid duplicates)
        normalized_email = data.email.lower().strip()
        
        # Check if user already exists
        existing_user = self.db.query(User).filter(User.email == normalized_email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        # Hash password
        password_hash = hash_password(data.password)
        
        # Determine timezone (use provided or default)
        user_timezone = data.timezone or settings.DEFAULT_TIMEZONE or "Asia/Kolkata"
        
        # ⚠️ CRITICAL: Validate timezone to prevent Postgres errors
        # Invalid timezone strings can break Postgres AT TIME ZONE queries
        # Note: This is a double-check (schema already validates), but good for safety
        import pytz
        if user_timezone not in pytz.all_timezones:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid timezone: {user_timezone}. Must be a valid IANA timezone."
            )
        
        # Create user
        user = User(
            id=uuid.uuid4(),
            email=normalized_email,  # Use normalized email (lowercase + strip)
            password_hash=password_hash,
            units="kg",  # Default units
            timezone=user_timezone,
            default_rest_timer_seconds=90  # Default rest timer
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        refresh_token_obj, raw_refresh_token = create_refresh_token(user.id, self.db)
        self.db.commit()

        access_token = create_access_token(user.id)
        return user, access_token, raw_refresh_token

    def login(self, data: LoginIn) -> Tuple[User, str]:
        """
        Login user.
        
        Args:
            data: Login data (email, password)
        
        Returns:
            Tuple of (User, JWT token)
        
        Raises:
            HTTPException: If credentials invalid
        """
        # ⚠️ CRITICAL: Normalize email (lowercase + strip)
        normalized_email = data.email.lower().strip()
        
        # Find user by email
        user = self.db.query(User).filter(User.email == normalized_email).first()
        
        if not user:
            # Don't reveal if email exists (security best practice)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        refresh_token_obj, raw_refresh_token = create_refresh_token(user.id, self.db)
        self.db.commit()

        access_token = create_access_token(user.id)
        return user, access_token, raw_refresh_token

    def get_or_create_demo_user(self) -> User:
        """
        Get or create the demo user (demo@example.com). Single mode: always available.
        Password from DEMO_USER_PASSWORD env (default 'demo' in dev).
        """
        from app.config.settings import settings
        demo_email = "demo@example.com"
        user = self.db.query(User).filter(User.email == demo_email).first()
        if user:
            return user
        password = getattr(settings, "DEMO_USER_PASSWORD", None) or "demo"
        password_hash = hash_password(password)
        user = User(
            id=uuid.uuid4(),
            email=demo_email,
            password_hash=password_hash,
            units="kg",
            timezone=settings.DEFAULT_TIMEZONE or "Asia/Kolkata",
            default_rest_timer_seconds=90,
            email_verified=True,
            entitlement="free",
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def issue_tokens_for_user(self, user: User) -> Tuple[str, str]:
        """Issue access and refresh tokens for an existing user (e.g. demo login). Returns (access_token, refresh_token)."""
        refresh_token_obj, raw_refresh_token = create_refresh_token(user.id, self.db)
        self.db.commit()
        access_token = create_access_token(user.id)
        return access_token, raw_refresh_token
