from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str
    ENVIRONMENT: str = "development"
    ABANDON_AFTER_HOURS: int = 24
    SECRET_KEY: str | None = None  # ⚠️ CRITICAL: No default - must be set
    
    # JWT Settings
    # ⚠️ CRITICAL: No default secret - must be set in environment
    # In production, this MUST be set or app will crash on startup
    JWT_SECRET_KEY: str | None = None
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_DAYS: int = 7
    JWT_ISSUER: str = "fitness-api"  # Token issuer (prevents token confusion if multiple services)
    JWT_AUDIENCE: str = "fitness-mobile"  # Token audience (prevents token confusion if multiple clients)
    
    # Timezone Settings
    DEFAULT_TIMEZONE: str = "Asia/Kolkata"  # ⚠️ CRITICAL: Default timezone for new users

    # Email (AWS SES) — Phase 2 Week 1
    EMAIL_DEV_MODE: bool = True  # If True, log OTP instead of sending (dev)
    SES_SENDER_EMAIL: str = "noreply@example.com"  # Set in production
    SES_REGION: str = "us-east-1"
    REFRESH_TOKEN_PEPPER: str | None = None  # Optional pepper for refresh token hashing

    # Bedrock (Phase 2 Week 5 — Coach AI)
    # boto3 reads AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY from env; declare here so .env is allowed
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str = "us-east-1"
    BEDROCK_MODEL_ID_DAILY: str | None = None  # e.g. anthropic.claude-3-haiku-20240307-v1:0
    BEDROCK_MODEL_ID_LITE: str | None = None  # Optional fallback (smaller model)
    BEDROCK_MAX_TOKENS: int = 1024
    BEDROCK_TEMPERATURE: float = 0.7
    BEDROCK_TOP_P: float = 0.9
    # Coach-only: lower temperature for grounded, non-hallucinating replies
    COACH_TEMPERATURE: float = 0.35
    COACH_TOP_P: float = 0.85
    BEDROCK_TIMEOUT_SECONDS: int = 15
    BEDROCK_RETRY_COUNT: int = 2

    # Phase 3 — Portfolio mode (local refinement / job-ready demo)
    PORTFOLIO_MODE: bool = False  # When True: skip Pro checks for /ai/insights, /metrics/summary; demo seed/reset require X-DEMO-KEY
    DEMO_KEY: str | None = None  # Secret for X-DEMO-KEY header; required for POST /demo/seed and POST /demo/reset when PORTFOLIO_MODE=true
    DEMO_USER_PASSWORD: str | None = None  # Password for demo user (e.g. demo@example.com); used by POST /demo/login
    AI_ENABLED: bool = True  # Kill switch: when False, AI insights return fallback only (no LLM)

    # Coach chat retention: delete messages older than this many days (0 = keep forever). 1 = new day, new messages.
    COACH_CHAT_RETENTION_DAYS: int = 1

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


# Allowed Bedrock regions for Claude (validate at startup when Bedrock is configured)
BEDROCK_ALLOWED_REGIONS = frozenset({"us-east-1", "us-west-2", "ap-southeast-1", "eu-central-1", "eu-west-2"})


settings = Settings()

# ⚠️ CRITICAL: Validate required secrets in production
if settings.ENVIRONMENT != "development":
    if not settings.JWT_SECRET_KEY:
        raise ValueError(
            "JWT_SECRET_KEY must be set in production environment. "
            "Set it in .env file or environment variables."
        )
    if not settings.SECRET_KEY:
        raise ValueError(
            "SECRET_KEY must be set in production environment. "
            "Set it in .env file or environment variables."
        )
# For development, allow None but warn
elif not settings.JWT_SECRET_KEY:
    import warnings
    warnings.warn(
        "JWT_SECRET_KEY not set. Using default dev secret. "
        "Set JWT_SECRET_KEY in .env for production.",
        UserWarning
    )
    settings.JWT_SECRET_KEY = "dev-jwt-secret-change-in-production"
if not settings.SECRET_KEY:
    import warnings
    warnings.warn(
        "SECRET_KEY not set. Using default dev secret. "
        "Set SECRET_KEY in .env for production.",
        UserWarning
    )
    settings.SECRET_KEY = "dev-secret-key-change-in-production"

# Bedrock: validate region only when daily model is configured
if settings.BEDROCK_MODEL_ID_DAILY and settings.AWS_REGION not in BEDROCK_ALLOWED_REGIONS:
    raise ValueError(
        f"AWS_REGION must be one of {sorted(BEDROCK_ALLOWED_REGIONS)} for Bedrock Claude. "
        f"Got: {settings.AWS_REGION!r}"
    )
