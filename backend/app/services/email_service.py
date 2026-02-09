"""Email service for sending transactional emails."""
import logging

from app.config.settings import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Send transactional emails via AWS SES (or dev fallback)."""

    def send_otp(self, to_email: str, otp: str) -> bool:
        """
        Send OTP verification email.

        In dev mode (EMAIL_DEV_MODE=true), logs OTP instead of sending.
        """
        if getattr(settings, "EMAIL_DEV_MODE", True):
            # Do not log OTP value (Phase 2 Week 8: logging sanitization)
            logger.warning("[DEV MODE] OTP sent to %s*** (check console for code)", to_email[:3] if len(to_email) >= 3 else "***")
            print(f"\n{'='*50}")
            print(f"DEV MODE - OTP CODE: {otp}")
            print(f"Email: {to_email}")
            print(f"{'='*50}\n")
            return True

        try:
            import boto3
            from botocore.config import Config

            client = boto3.client(
                "ses",
                region_name=getattr(settings, "SES_REGION", "us-east-1"),
                config=Config(retries={"max_attempts": 2}),
            )

            subject = "Your verification code"
            body = f"""
Your verification code is: {otp}

This code expires in 10 minutes.

If you didn't request this, please ignore this email.
            """.strip()

            client.send_email(
                Source=settings.SES_SENDER_EMAIL,
                Destination={"ToAddresses": [to_email]},
                Message={
                    "Subject": {"Data": subject},
                    "Body": {"Text": {"Data": body}},
                },
            )
            logger.info("OTP sent to %s***", to_email[:3])
            return True

        except Exception as e:
            logger.error("Failed to send OTP: %s", type(e).__name__)
            return False


email_service = EmailService()
