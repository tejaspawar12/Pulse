"""
Comprehensive test for Day 4 deliverables:
1. GET /me/status endpoint
2. Active workout summary
3. Today's workout status
4. Last 30 days workout history
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
from app.utils.enums import LifecycleStatus, CompletionStatus
from datetime import datetime, timezone, timedelta
from sqlalchemy import text
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

print("🧪 Day 4 Comprehensive Test\n")

# Test 1: GET /me/status with no active workout
print("1. Testing GET /me/status (no active workout)...")
# CRITICAL FIX: Abandon any existing drafts from Day 3 tests
db = SessionLocal()
db.query(Workout).filter(
    Workout.user_id == test_user.id,
    Workout.lifecycle_status == LifecycleStatus.DRAFT.value
).update({Workout.lifecycle_status: LifecycleStatus.ABANDONED.value})
db.commit()
db.close()

response = client.get("/api/v1/me/status", headers=headers)
assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
data = response.json()
assert data["active_workout"] is None, "Should have no active workout"
assert "today_worked_out" in data, "Should have today_worked_out field"
assert "last_30_days" in data, "Should have last_30_days field"
assert len(data["last_30_days"]) == 30, "Should have 30 days"
print("   ✅ Status endpoint works (no active workout)\n")

# Test 2: Start workout and check status
print("2. Testing GET /me/status with active workout...")
# Start a workout
start_response = client.post("/api/v1/workouts/start", headers=headers)
assert start_response.status_code == 200
workout_id = start_response.json()["id"]

# Get status
status_response = client.get("/api/v1/me/status", headers=headers)
assert status_response.status_code == 200
status_data = status_response.json()
assert status_data["active_workout"] is not None, "Should have active workout"
assert status_data["active_workout"]["id"] == workout_id, "Should match workout ID"
assert "date" in status_data["active_workout"], "Should have date"
assert "start_time" in status_data["active_workout"], "Should have start_time"
assert "exercise_count" in status_data["active_workout"], "Should have exercise_count"
assert "set_count" in status_data["active_workout"], "Should have set_count"
print("   ✅ Status endpoint works (with active workout)\n")

# Test 3: Verify last 30 days structure
print("3. Testing last 30 days structure...")
assert isinstance(status_data["last_30_days"], list), "Should be a list"
assert len(status_data["last_30_days"]) == 30, "Should have 30 days"
for day in status_data["last_30_days"]:
    assert "date" in day, "Each day should have date"
    assert "worked_out" in day, "Each day should have worked_out"
    assert isinstance(day["worked_out"], bool), "worked_out should be boolean"
print("   ✅ Last 30 days structure correct\n")

# Test 4: Create finalized workout and verify it appears
print("4. Testing finalized workout appears in history...")
db = SessionLocal()
# Abandon any existing drafts
db.query(Workout).filter(
    Workout.user_id == test_user.id,
    Workout.lifecycle_status == LifecycleStatus.DRAFT.value
).update({Workout.lifecycle_status: LifecycleStatus.ABANDONED.value})
db.commit()

# Create a finalized workout from yesterday (in user timezone)
# Get user timezone first
user_timezone = test_user.timezone or "Asia/Kolkata"
yesterday_utc = datetime.now(timezone.utc) - timedelta(days=1)

finalized_workout = Workout(
    id=uuid.uuid4(),
    user_id=test_user.id,
    lifecycle_status=LifecycleStatus.FINALIZED.value,
    completion_status=CompletionStatus.COMPLETED.value,
    start_time=yesterday_utc,
    end_time=yesterday_utc + timedelta(minutes=45),
    duration_minutes=45
)
db.add(finalized_workout)
db.commit()

# Compute yesterday's date in user timezone for assertion
yesterday_date_query = text("SELECT DATE(timezone(:tz, :start_time)) as workout_date")
yesterday_date_result = db.execute(
    yesterday_date_query,
    {"tz": user_timezone, "start_time": yesterday_utc}
)
yesterday_date = yesterday_date_result.scalar()
db.close()

# Get status again
status_response = client.get("/api/v1/me/status", headers=headers)
assert status_response.status_code == 200
status_data = status_response.json()

# CRITICAL FIX: Check specific date (not just "any day")
# Find yesterday's date in last_30_days and verify it has worked_out=True
yesterday_in_list = next(
    (day for day in status_data["last_30_days"] if day["date"] == yesterday_date.isoformat()),
    None
)
assert yesterday_in_list is not None, f"Yesterday ({yesterday_date}) should be in last_30_days"
assert yesterday_in_list["worked_out"] is True, f"Yesterday ({yesterday_date}) should have worked_out=True"
print(f"   ✅ Finalized workout appears in history for date: {yesterday_date}\n")

print("🎉 All Day 4 tests passed!")
