"""
Print the test user's UUID for use in X-DEV-USER-ID (e.g. in PowerShell).
Usage: python scripts/get_test_user_id.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.database import SessionLocal
from app.models.user import User

def main():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "test@example.com").first()
        if user:
            print(str(user.id))
        else:
            print("No test user. Run: python scripts/create_test_user.py", file=sys.stderr)
            sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
