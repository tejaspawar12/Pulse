"""Tests for OTP verification (Phase 2 Week 1)."""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import pytest

from app.models.email_verification_otp import EmailVerificationOTP
from app.services.otp_service import (
    generate_otp,
    hash_otp,
    request_otp,
    verify_otp,
)


def test_generate_otp():
    """OTP is 6 digits."""
    otp = generate_otp()
    assert len(otp) == 6
    assert otp.isdigit()
    assert 100000 <= int(otp) <= 999999


def test_hash_otp_deterministic():
    """Same OTP produces same hash."""
    assert hash_otp("123456") == hash_otp("123456")
    assert hash_otp("123456") != hash_otp("654321")


@patch("app.services.otp_service.email_service.send_otp")
def test_request_otp_success(mock_send_otp, db, test_user):
    """request_otp creates OTP and returns success when email sends."""
    mock_send_otp.return_value = True
    result = request_otp(test_user.id, test_user.email, db)
    assert result["success"] is True
    assert "sent" in result["message"].lower() or "verification" in result["message"].lower()
    count = db.query(EmailVerificationOTP).filter(EmailVerificationOTP.user_id == test_user.id).count()
    assert count >= 1


def test_verify_otp_success(db, test_user):
    """verify_otp with correct code marks user verified and can start trial."""
    now = datetime.now(timezone.utc)
    code = "123456"
    otp_record = EmailVerificationOTP(
        user_id=test_user.id,
        otp_hash=hash_otp(code),
        expires_at=now + timedelta(minutes=10),
    )
    db.add(otp_record)
    db.commit()

    result = verify_otp(test_user.id, code, db)
    assert result["success"] is True
    db.refresh(test_user)
    assert test_user.email_verified is True
    assert result.get("trial_started") in (True, False)
    if result.get("trial_started"):
        assert result.get("trial_ends_at") is not None


def test_verify_otp_wrong_code(db, test_user):
    """verify_otp with wrong code returns failure."""
    now = datetime.now(timezone.utc)
    otp_record = EmailVerificationOTP(
        user_id=test_user.id,
        otp_hash=hash_otp("123456"),
        expires_at=now + timedelta(minutes=10),
    )
    db.add(otp_record)
    db.commit()

    result = verify_otp(test_user.id, "999999", db)
    assert result["success"] is False
    assert "invalid" in result["message"].lower() or "attempts" in result["message"].lower()
    db.refresh(test_user)
    assert test_user.email_verified is False


def test_verify_otp_expired(db, test_user):
    """verify_otp with expired OTP returns no valid code."""
    now = datetime.now(timezone.utc)
    otp_record = EmailVerificationOTP(
        user_id=test_user.id,
        otp_hash=hash_otp("123456"),
        expires_at=now - timedelta(minutes=1),
    )
    db.add(otp_record)
    db.commit()

    result = verify_otp(test_user.id, "123456", db)
    assert result["success"] is False
    assert "valid" in result["message"].lower() or "new" in result["message"].lower()
