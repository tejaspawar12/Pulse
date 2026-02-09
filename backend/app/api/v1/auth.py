"""
Authentication API endpoints.
Phase 2 Week 8: Rate limit login (5/min by IP); request-otp already returns 429 from OTP service.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user_auto
from app.utils.rate_limit import check_rate_limit
from app.config.settings import settings
from app.models.user import User
from app.schemas.auth import (
    AuthOut,
    LoginIn,
    LogoutRequest,
    OTPVerify,
    RefreshRequest,
    RegisterIn,
    TokenResponse,
)
from app.schemas.user import UserOut
from app.services.auth_service import (
    AuthService,
    refresh_access_token,
    revoke_all_user_tokens,
    revoke_refresh_token,
)
from app.services.otp_service import request_otp, verify_otp

router = APIRouter()


@router.post("/auth/register", response_model=AuthOut, status_code=status.HTTP_201_CREATED)
def register(
    data: RegisterIn,
    db: Session = Depends(get_db),
):
    """
    Register new user.

    Creates a new user account and returns JWT access token, refresh token, and user data.
    """
    service = AuthService(db)
    user, access_token, refresh_token = service.register(data)

    expires_in = settings.JWT_EXPIRATION_DAYS * 24 * 60 * 60
    return AuthOut(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserOut.model_validate(user),
    )


LOGIN_RATE_LIMIT_PER_MINUTE = 5
LOGIN_RATE_WINDOW_SECONDS = 60


@router.post("/auth/login", response_model=AuthOut)
def login(
    request: Request,
    data: LoginIn,
    db: Session = Depends(get_db),
):
    """
    Login user.

    Authenticates user and returns JWT access token, refresh token, and user data.
    Rate limited: 5 attempts per minute per IP (Phase 2 Week 8).
    """
    client_ip = request.client.host if request.client else "unknown"
    key = f"auth:login:{client_ip}"
    count = check_rate_limit(key, LOGIN_RATE_LIMIT_PER_MINUTE, LOGIN_RATE_WINDOW_SECONDS)
    if count > LOGIN_RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again in a few minutes.",
        )
    service = AuthService(db)
    user, access_token, refresh_token = service.login(data)

    expires_in = settings.JWT_EXPIRATION_DAYS * 24 * 60 * 60
    return AuthOut(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserOut.model_validate(user),
    )


@router.post("/auth/refresh", response_model=TokenResponse)
def refresh_token(
    request: RefreshRequest,
    db: Session = Depends(get_db),
):
    """Exchange refresh token for new access + refresh tokens (token rotation)."""
    try:
        tokens = refresh_access_token(request.refresh_token, db)
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/auth/logout")
def logout(
    request: LogoutRequest,
    db: Session = Depends(get_db),
):
    """Revoke current refresh token."""
    revoked = revoke_refresh_token(request.refresh_token, db)
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token not found",
        )
    return {"message": "Logged out successfully"}


@router.post("/auth/logout-all")
def logout_all(
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
):
    """Revoke all refresh tokens for the current user (all sessions)."""
    count = revoke_all_user_tokens(current_user.id, db)
    return {"message": f"Revoked {count} sessions"}


@router.post("/auth/request-otp")
def request_otp_endpoint(
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
):
    """Request OTP for email verification (sends to current user's email)."""
    if current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified",
        )
    result = request_otp(current_user.id, current_user.email, db)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=result["message"],
        )
    return result


@router.post("/auth/verify-otp")
def verify_otp_endpoint(
    request: OTPVerify,
    current_user: User = Depends(get_current_user_auto),
    db: Session = Depends(get_db),
):
    """Verify OTP and activate email verification (starts 7-day trial if first time)."""
    result = verify_otp(current_user.id, request.otp, db)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"],
        )
    return result


# ⏳ OPTIONAL: Future enhancement - /auth/me shortcut endpoint
# Instead of reusing /users/me, can add:
# @router.get("/auth/me", response_model=UserOut)
# def get_current_user_profile_auth(
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Get current user profile (auth-specific endpoint)."""
#     return UserOut.model_validate(current_user)
# Not required for MVP, but can be added later for cleaner API design
