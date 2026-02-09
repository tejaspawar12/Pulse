from typing import Generator, Optional
import uuid
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.models.user import User
from app.utils.auth import decode_access_token
from app.utils.entitlement import has_pro_access, requires_email_verification
# Import all models to ensure SQLAlchemy can resolve relationships
from app.models.exercise import ExerciseLibrary
from app.models.workout import Workout, WorkoutExercise, WorkoutSet

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user_dev(
    x_dev_user_id: str = Header(..., alias="X-DEV-USER-ID"),
    db: Session = Depends(get_db),
) -> User:
    """
    Dev mode: Get user from X-DEV-USER-ID header.
    
    For production, replace with JWT authentication.
    
    Args:
        x_dev_user_id: User ID from X-DEV-USER-ID header
        db: Database session
    
    Returns:
        User: Current user
    
    Raises:
        HTTPException: If user ID is invalid or user not found
    """
    try:
        user_id = uuid.UUID(x_dev_user_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID format. Must be a valid UUID."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return user

# JWT Bearer token security
# ⚠️ CRITICAL: Use auto_error=False to handle missing tokens with custom 401 message
# Default HTTPBearer() can return confusing 403 errors
security = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user from JWT token.
    
    For production use. Dev mode can use get_current_user_dev.
    
    Args:
        credentials: HTTP Bearer token credentials (None if missing)
        db: Database session
    
    Returns:
        User: Current user
    
    Raises:
        HTTPException: If token missing, invalid, expired, or user not found
    """
    # Handle missing token
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    # Decode token (returns tuple: user_id, error_code)
    user_id, error_code = decode_access_token(token)
    
    if user_id is None:
        # Distinguish expired vs invalid for better error messages
        if error_code == "expired":
            detail = "Token has expired"
        else:
            detail = "Invalid token"
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

# Helper to choose auth method based on environment
def get_current_user_auto(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_dev_user_id: Optional[str] = Header(None, alias="X-DEV-USER-ID")
) -> User:
    """
    Auto-select auth method: JWT if Authorization header present, else dev auth.
    
    Useful for gradual migration or local development.
    
    Args:
        db: Database session
        authorization: Authorization header (Bearer token)
        x_dev_user_id: Dev user ID header
    
    Returns:
        User: Current user
    """
    # Try JWT first if Authorization header present
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        user_id, error_code = decode_access_token(token)
        if user_id is None:
            # Token is invalid or expired - raise appropriate error
            if error_code == "expired":
                detail = "Token has expired"
            else:
                detail = "Invalid token"
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=detail,
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Token is valid, get user
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            return user
        # User not found
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fall back to dev auth
    if x_dev_user_id:
        try:
            user_id = UUID(x_dev_user_id)
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                return user
        except ValueError:
            pass
    
    # No valid auth found
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required"
    )


def require_pro(user: User) -> User:
    """Dependency that raises 403 if user doesn't have Pro access."""
    if not has_pro_access(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Pro subscription required",
            headers={"X-Upgrade-Required": "true"},
        )
    return user


def require_verified_email(user: User) -> User:
    """Dependency that raises 403 if email not verified."""
    if requires_email_verification(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required",
            headers={"X-Verify-Email": "true"},
        )
    return user


def get_current_pro_user(
    current_user: User = Depends(get_current_user_auto),
) -> User:
    """Get current user and verify Pro access (for premium-only endpoints)."""
    return require_pro(current_user)
