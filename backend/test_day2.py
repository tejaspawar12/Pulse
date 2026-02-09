"""
Comprehensive test for Day 2 deliverables:
1. Exercise seed
2. Dev auth
"""
from app.config.database import SessionLocal
from app.models.exercise import ExerciseLibrary
from app.models.user import User
from app.api.deps import get_db, get_current_user_dev
from fastapi.testclient import TestClient
from app.main import app
import uuid

print("🧪 Day 2 Comprehensive Test\n")

# Test 1: Exercise seed
print("1. Testing exercise seed...")
db = SessionLocal()
exercise_count = db.query(ExerciseLibrary).count()
print(f"   ✅ Exercises in database: {exercise_count}")
assert exercise_count == 58, f"Expected 58 exercises, got {exercise_count}"
print("   ✅ Exercise count correct\n")

# Test 2: Exercise data quality
print("2. Testing exercise data quality...")
sample = db.query(ExerciseLibrary).first()
assert sample.normalized_name == sample.name.lower().strip(), "Normalized name incorrect"
assert sample.primary_muscle_group in ["chest", "back", "shoulders", "arms", "legs", "core", "full_body"]
assert sample.equipment in ["barbell", "dumbbell", "machine", "cable", "bodyweight", "kettlebell", "other"]
assert sample.movement_type in ["strength", "cardio"]
print("   ✅ Exercise data quality checks passed\n")

# Test 3: Test user exists
print("3. Testing test user...")
test_user = db.query(User).filter(User.email == "test@example.com").first()
assert test_user is not None, "Test user not found"
print(f"   ✅ Test user exists: {test_user.email}")
print(f"   ✅ User ID: {test_user.id}\n")

# Test 4: Dev auth
print("4. Testing dev auth...")
client = TestClient(app)

# Test without header (should fail)
response = client.get("/api/v1/test-auth")
assert response.status_code == 422, "Should require X-DEV-USER-ID header"
print("   ✅ Auth required (no header fails)")

# Test with invalid user ID
response = client.get(
    "/api/v1/test-auth",
    headers={"X-DEV-USER-ID": str(uuid.uuid4())}
)
assert response.status_code == 404, "Should return 404 for invalid user"
print("   ✅ Invalid user ID handled")

# Test with valid user ID
response = client.get(
    "/api/v1/test-auth",
    headers={"X-DEV-USER-ID": str(test_user.id)}
)
assert response.status_code == 200, "Should work with valid user ID"
print("   ✅ Valid user ID works\n")

db.close()

print("🎉 All Day 2 tests passed!")
