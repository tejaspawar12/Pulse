"""
Test dev authentication with FastAPI TestClient.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.config.database import SessionLocal
from app.models.user import User
import uuid

client = TestClient(app)

# Get test user ID
db = SessionLocal()
test_user = db.query(User).filter(User.email == "test@example.com").first()
db.close()

if not test_user:
    print("❌ Test user not found. Run create_test_user.py first.")
    exit(1)

user_id = str(test_user.id)
print(f"Testing with user ID: {user_id}\n")

# Test root endpoint (no auth)
print("1. Testing root endpoint (no auth required)...")
response = client.get("/")
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}\n")

# Test endpoint with dev auth
print("2. Testing endpoint with dev auth...")
response = client.get(
    "/api/v1/test-auth",
    headers={"X-DEV-USER-ID": user_id}
)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print(f"   Response: {response.json()}")
else:
    print(f"   Error: {response.text}")

print("\n✅ Dev auth test complete!")
