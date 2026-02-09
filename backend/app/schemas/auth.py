"""
Authentication schemas.
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional
from uuid import UUID

class RegisterIn(BaseModel):
    """Request schema for user registration."""
    model_config = ConfigDict(from_attributes=True)
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=100, description="Password (min 8 characters)")
    timezone: Optional[str] = Field(None, description="User timezone (IANA timezone string, optional)")
    
    @field_validator('timezone')
    @classmethod
    def validate_timezone(cls, v: Optional[str]) -> Optional[str]:
        """Validate timezone using pytz (optional but cleaner errors)."""
        if v is None:
            return v
        import pytz
        if v not in pytz.all_timezones:
            raise ValueError(f"Invalid timezone: {v}. Must be a valid IANA timezone.")
        return v

class LoginIn(BaseModel):
    """Request schema for user login."""
    model_config = ConfigDict(from_attributes=True)
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

class TokenResponse(BaseModel):
    """Response for login/register or refresh with access + refresh token."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Request to refresh access token."""
    refresh_token: str


class LogoutRequest(BaseModel):
    """Request to logout (revoke refresh token)."""
    refresh_token: str


class OTPRequest(BaseModel):
    """Request to send OTP (uses authenticated user's email)."""
    pass


class OTPVerify(BaseModel):
    """Request to verify OTP."""
    otp: str


class AuthOut(BaseModel):
    """Response schema for authentication (register/login)."""
    model_config = ConfigDict(from_attributes=True)

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="Refresh token for obtaining new access tokens")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds (604800 = 7 days)")
    user: "UserOut" = Field(..., description="User profile data")

# Forward reference - UserOut is defined in user.py
from app.schemas.user import UserOut
AuthOut.model_rebuild()
