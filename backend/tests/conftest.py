"""
Pytest configuration and fixtures for integration tests.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

# Option A: Use Postgres in Docker (recommended - matches production)
# Set TEST_DATABASE_URL in environment or use default
import os

# Set DATABASE_URL before importing app to satisfy Settings validation
SQLALCHEMY_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/fitness_test"
)
# Set DATABASE_URL for app settings (required by Settings class)
os.environ["DATABASE_URL"] = SQLALCHEMY_DATABASE_URL

from app.main import app
from app.api.deps import get_db
from app.models.base import Base
from app.models.user import User
from app.models.exercise import ExerciseLibrary
from app.models.refresh_token import RefreshToken  # Phase 2 Week 1 — ensure table created
from app.models.email_verification_otp import EmailVerificationOTP  # Phase 2 Week 1 — OTP table
from app.models.push_subscription import PushSubscription  # Phase 2 Week 2 — push table

# Option B: Use SQLite (faster, but must ensure no Postgres-only types)
# SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# For Postgres:
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# For SQLite (if using Option B):
# engine = create_engine(
#     SQLALCHEMY_DATABASE_URL,
#     connect_args={"check_same_thread": False},
#     poolclass=StaticPool,
# )
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def setup_db():
    """
    Create database schema once per test session (not per test).
    Drops then recreates tables so schema always matches current models
    (e.g. new columns like email_verified, entitlement are present).
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(scope="function")
def db(setup_db):
    """
    Create isolated database session for each test using nested transactions.
    
    ⚠️ CRITICAL: For Postgres, endpoints call db.commit() internally.
    Simple transaction.rollback() won't work because commits close the transaction.
    
    ✅ Solution: Use nested transactions (SAVEPOINT) so commits inside endpoints
    don't end the outer isolation. This makes tests fast and isolated.
    
    Alternative options (if nested transactions don't work):
    - Option B: Use separate test database and run tests serially
    - Option C: Use SQLite in-memory (faster, but must ensure no Postgres-only types)
    - Option D: Keep drop_all() (slow but predictable)
    """
    # Connect to database and start outer transaction
    connection = engine.connect()
    transaction = connection.begin()  # Outer transaction
    
    # Create session bound to this connection
    session = TestingSessionLocal(bind=connection)
    
    # Start a nested transaction (SAVEPOINT)
    # This allows commits inside endpoints without ending outer transaction
    session.begin_nested()
    
    # Restart savepoint after each commit (endpoints commit internally)
    # ⚠️ LOCKED: Use event.listen/remove (not decorator) to prevent listener stacking
    def restart_savepoint(sess, trans):
        if trans.nested and not trans._parent.nested:
            sess.begin_nested()
    
    event.listen(session, "after_transaction_end", restart_savepoint)
    
    try:
        yield session
    finally:
        # ⚠️ CRITICAL: Remove listener before closing to prevent flakiness
        event.remove(session, "after_transaction_end", restart_savepoint)
        session.close()
        transaction.rollback()  # Rollback outer transaction (cleans everything)
        connection.close()


@pytest.fixture(scope="function")
def client(db):
    """
    Create test client with database override.
    
    ⚠️ CRITICAL: Must use the same db session bound to the connection.
    Otherwise, endpoints might use a different connection/session and rollback doesn't apply.
    """
    def override_get_db():
        try:
            yield db  # Use the session bound to the connection (from db fixture)
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db):
    """Create test user."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        password_hash="hashed",
        units="kg",
        timezone="UTC"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_exercise(db):
    """Create test exercise."""
    exercise = ExerciseLibrary(
        id=uuid4(),
        name="Bench Press",
        primary_muscle_group="chest",
        equipment="barbell",
        movement_type="push",
        normalized_name="bench press"
    )
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return exercise


@pytest.fixture(scope="function")
def auth_headers(test_user):
    """Create auth headers for test user."""
    return {"X-DEV-USER-ID": str(test_user.id)}


# ⚠️ LOCKED: finalize_workout() is ONLY in helpers.py, NOT in conftest.py
# This avoids import confusion and keeps tests clean.
# Import it as: from tests.helpers import finalize_workout
# See section 1.1.1 for helpers.py implementation
