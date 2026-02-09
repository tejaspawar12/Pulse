"""OTP service for email verification."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.email_verification_otp import EmailVerificationOTP
from app.models.user import User
from app.services.email_service import email_service
from app.utils.rate_limit import get_rate_limit_store

OTP_EXPIRY_MINUTES = 10
MAX_FAILED_ATTEMPTS = 5


def hash_otp(otp: str) -> str:
    """Hash OTP using SHA-256."""
    return hashlib.sha256(otp.encode()).hexdigest()


def generate_otp() -> str:
    """Generate a 6-digit OTP."""
    return str(secrets.randbelow(900000) + 100000)


def request_otp(user_id: UUID, email: str, db: Session) -> dict:
    """
    Generate and send OTP for email verification.

    Returns:
        dict with success and message
    """
    rate_limiter = get_rate_limit_store()

    hour_key = f"otp_hour:{user_id}"
    day_key = f"otp_day:{user_id}"

    hour_count = rate_limiter.increment(hour_key, 3600)
    if hour_count > 3:
        return {"success": False, "message": "Too many requests. Try again in an hour."}

    day_count = rate_limiter.increment(day_key, 86400)
    if day_count > 10:
        return {"success": False, "message": "Daily limit reached. Try again tomorrow."}

    now = datetime.now(timezone.utc)
    db.query(EmailVerificationOTP).filter(
        EmailVerificationOTP.user_id == user_id,
        EmailVerificationOTP.verified_at.is_(None),
        EmailVerificationOTP.invalidated_at.is_(None),
    ).update({"invalidated_at": now}, synchronize_session=False)

    db.flush()

    otp = generate_otp()
    otp_hash_val = hash_otp(otp)

    otp_record = EmailVerificationOTP(
        user_id=user_id,
        otp_hash=otp_hash_val,
        expires_at=now + timedelta(minutes=OTP_EXPIRY_MINUTES),
    )
    db.add(otp_record)
    db.commit()

    sent = email_service.send_otp(email, otp)
    if not sent:
        return {"success": False, "message": "Failed to send email. Try again."}

    return {"success": True, "message": "Verification code sent to your email."}


def verify_otp(user_id: UUID, otp: str, db: Session) -> dict:
    """
    Verify OTP and activate email verification.

    Returns:
        dict with success, message, trial_started, trial_ends_at
    """
    now = datetime.now(timezone.utc)

    stored_otp = (
        db.query(EmailVerificationOTP)
        .filter(
            EmailVerificationOTP.user_id == user_id,
            EmailVerificationOTP.verified_at.is_(None),
            EmailVerificationOTP.invalidated_at.is_(None),
            EmailVerificationOTP.expires_at > now,
        )
        .order_by(
            EmailVerificationOTP.created_at.desc(),
            EmailVerificationOTP.id.desc(),
        )
        .first()
    )

    if not stored_otp:
        return {"success": False, "message": "No valid verification code found. Request a new one."}

    if stored_otp.failed_attempts >= MAX_FAILED_ATTEMPTS:
        stored_otp.invalidated_at = now
        db.commit()
        return {"success": False, "message": "Too many failed attempts. Request a new code."}

    if hash_otp(otp) != stored_otp.otp_hash:
        stored_otp.failed_attempts += 1
        db.commit()
        remaining = MAX_FAILED_ATTEMPTS - stored_otp.failed_attempts
        return {"success": False, "message": f"Invalid code. {remaining} attempts remaining."}

    stored_otp.verified_at = now

    user = db.get(User, user_id)
    if not user:
        db.commit()
        return {"success": False, "message": "User not found."}

    user.email_verified = True

    started_now = not user.trial_used
    if started_now:
        user.pro_trial_ends_at = now + timedelta(days=7)
        user.trial_used = True

    db.commit()

    return {
        "success": True,
        "message": "Email verified successfully!",
        "trial_started": started_now,
        "trial_ends_at": user.pro_trial_ends_at.isoformat() if user.pro_trial_ends_at else None,
    }
