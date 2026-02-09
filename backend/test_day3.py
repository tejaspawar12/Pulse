"""
Comprehensive test for Day 3 deliverables:
1. Health endpoint
2. Start workout endpoint
3. Get active workout endpoint
4. Auto-abandonment logic
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.config.database import SessionLocal
# Import all models so SQLAlchemy can resolve relationships
from app.models.user import User
from app.models.exercise import ExerciseLibrary
from app.models.workout import Workout, WorkoutExercise, WorkoutSet
from app.models.daily_training_state import DailyTrainingState
from app.utils.enums import LifecycleStatus
from datetime import datetime, timezone, timedelta
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
headers = {"X-DEV-USER-ID": user_id}

print("🧪 Day 3 Comprehensive Test\n")

# Test 1: Health endpoint
print("1. Testing health endpoint...")
response = client.get("/api/v1/health")
assert response.status_code == 200, f"Expected 200, got {response.status_code}"
data = response.json()
assert data["status"] == "ok", "Health check should return ok"
assert data["database"] == "connected", "Database should be connected"
print("   ✅ Health endpoint works\n")

# Test 2: Start workout
print("2. Testing POST /workouts/start...")
response = client.post("/api/v1/workouts/start", headers=headers)
assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
data = response.json()
assert data["lifecycle_status"] == "draft", "Workout should be draft (enum serialized as string)"
assert "start_time" in data, "Workout should have start_time"
workout_id = data["id"]
print(f"   ✅ Workout started: {workout_id}\n")

# Test 3: Get active workout
print("3. Testing GET /workouts/active...")
response = client.get("/api/v1/workouts/active", headers=headers)
assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
data = response.json()
assert data is not None, "Should return workout (not null, returns 200 not 204)"
assert data["id"] == workout_id, "Should return same workout"
assert data["lifecycle_status"] == "draft", "Should be draft (enum serialized as string)"
print("   ✅ Active workout retrieved\n")

# Test 4: Start workout again (should return existing)
print("4. Testing start workout again (should return existing)...")
response = client.post("/api/v1/workouts/start", headers=headers)
assert response.status_code == 200, "Should return existing workout"
data = response.json()
assert data["id"] == workout_id, "Should return same workout"
print("   ✅ Existing workout returned\n")

# Test 5: Auto-abandonment (create old draft)
print("5. Testing auto-abandonment logic...")
db = SessionLocal()
# First, abandon any existing drafts for this user
db.query(Workout).filter(
    Workout.user_id == test_user.id,
    Workout.lifecycle_status == LifecycleStatus.DRAFT.value
).update({Workout.lifecycle_status: LifecycleStatus.ABANDONED.value})
db.commit()

# Now create an old draft (25 hours old)
old_workout = Workout(
    id=uuid.uuid4(),
    user_id=test_user.id,
    lifecycle_status=LifecycleStatus.DRAFT.value,
    start_time=datetime.now(timezone.utc) - timedelta(hours=25)  # 25 hours old
)
db.add(old_workout)
db.commit()
old_workout_id = str(old_workout.id)
db.close()

# Try to start workout (should abandon old and create new)
response = client.post("/api/v1/workouts/start", headers=headers)
assert response.status_code == 200, "Should create new workout"
data = response.json()
assert data["id"] != old_workout_id, "Should create new workout, not return old"
print("   ✅ Old workout auto-abandoned\n")

# Verify old workout is abandoned
db = SessionLocal()
old = db.query(Workout).filter(Workout.id == uuid.UUID(old_workout_id)).first()
assert old.lifecycle_status == LifecycleStatus.ABANDONED.value, "Old workout should be abandoned"
assert old.completion_status is None, "Abandoned workout should have NULL completion_status"
db.close()
print("   ✅ Old workout marked as abandoned\n")

print("🎉 All Day 3 tests passed!")
