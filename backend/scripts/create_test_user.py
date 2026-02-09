"""
Script to create a test user for development.
Run this once to create a test user, then use the user ID in API requests.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.database import SessionLocal
from app.models.user import User
import uuid

# Always import bcrypt as fallback
try:
    import bcrypt
except ImportError:
    bcrypt = None

# Try to use passlib, fallback to direct bcrypt if passlib has issues
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    USE_PASSLIB = True
except Exception:
    USE_PASSLIB = False
    pwd_context = None

def create_test_user():
    """
    Create a test user for development.
    Returns the user ID for use in X-DEV-USER-ID header.
    """
    db = SessionLocal()
    try:
        # Check if test user already exists
        existing_user = db.query(User).filter(
            User.email == "test@example.com"
        ).first()
        
        if existing_user:
            print(f"✅ Test user already exists:")
            print(f"   ID: {existing_user.id}")
            print(f"   Email: {existing_user.email}")
            print(f"\n   Use this header in API requests:")
            print(f"   X-DEV-USER-ID: {existing_user.id}")
            return existing_user.id
        
        # Create new test user
        # Hash password - use bcrypt directly if passlib fails
        password = "test123"
        password_hash = None
        
        # Try passlib first if available
        if USE_PASSLIB:
            try:
                password_hash = pwd_context.hash(password)
            except Exception as e:
                print(f"⚠️  Passlib failed: {e}. Using bcrypt directly...")
                password_hash = None
        
        # Fallback to direct bcrypt if passlib failed or not available
        if password_hash is None:
            if bcrypt is None:
                raise ImportError("bcrypt is not installed. Run: pip install bcrypt")
            # Use bcrypt directly
            password_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            password_hash=password_hash,
            units="kg",
            timezone="Asia/Kolkata",
            default_rest_timer_seconds=90
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print(f"✅ Test user created successfully!")
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Password: test123")
        print(f"   Units: {user.units}")
        print(f"   Timezone: {user.timezone}")
        print(f"\n   Use this header in API requests:")
        print(f"   X-DEV-USER-ID: {user.id}")
        
        return user.id
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating test user: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()
