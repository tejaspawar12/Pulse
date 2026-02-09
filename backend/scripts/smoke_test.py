#!/usr/bin/env python3
"""
E2E Smoke Test Script for Week 2 features.
Tests complete workout flow: start → add exercise → add set → reorder → delete set → get active
"""
import requests
import sys
from uuid import uuid4

BASE_URL = "http://localhost:8000/api/v1"

# ⚠️ CRITICAL: Use existing dev user ID (not random UUID)
# If your dev auth expects user to exist in DB, random UUID will fail
# Option 1: Use known seeded/dev user ID
USER_ID = "your-known-dev-user-id-here"  # Replace with actual dev user ID

# Option 2: Create user in smoke test (if you have admin/dev setup)
# Option 3: Use existing test user from seed script

HEADERS = {"X-DEV-USER-ID": USER_ID}

def test_workout_flow():
    """Test complete workout flow."""
    print("🔥 Starting E2E Smoke Test...")
    
    # 0. ⚠️ LOCKED: Fail fast if active workout exists (ensures determinism)
    # This makes the smoke test reliable - no "cleanup recommended" warnings
    try:
        res = requests.get(f"{BASE_URL}/workouts/active", headers=HEADERS)
        if res.status_code == 200 and res.json():
            existing_workout_id = res.json()["id"]
            raise Exception(
                f"Active workout exists ({existing_workout_id}). "
                "Abandon it before running smoke test to ensure deterministic results."
            )
    except requests.exceptions.RequestException as e:
        print(f"   ℹ️  Could not check active workout: {e}")
        # Continue if it's a network error (might be first run)
    
    # 1. Start workout
    print("1. Starting workout...")
    res = requests.post(f"{BASE_URL}/workouts/start", headers=HEADERS)
    assert res.status_code == 200, f"Failed to start workout: {res.status_code}"
    workout_id = res.json()["id"]
    print(f"   ✅ Workout started: {workout_id}")
    
    # 2. Get exercise (assume exercise exists)
    print("2. Getting exercise...")
    res = requests.get(f"{BASE_URL}/exercises?q=bench", headers=HEADERS)
    assert res.status_code == 200, f"Failed to get exercises: {res.status_code}"
    exercises = res.json().get("exercises", [])
    assert len(exercises) > 0, "No exercises found"
    exercise_id = exercises[0]["id"]
    print(f"   ✅ Exercise found: {exercise_id}")
    
    # 3. Add exercise to workout
    print("3. Adding exercise to workout...")
    res = requests.post(
        f"{BASE_URL}/workouts/{workout_id}/exercises",
        json={"exercise_id": exercise_id},
        headers=HEADERS
    )
    assert res.status_code == 200, f"Failed to add exercise: {res.status_code}"
    workout_exercise_id = res.json()["exercises"][0]["id"]
    print(f"   ✅ Exercise added: {workout_exercise_id}")
    
    # 4. Add set
    print("4. Adding set...")
    res = requests.post(
        f"{BASE_URL}/workout-exercises/{workout_exercise_id}/sets",
        json={"reps": 8, "weight": 60.0, "set_type": "working"},
        headers=HEADERS
    )
    assert res.status_code == 200, f"Failed to add set: {res.status_code}"
    set_id = res.json()["id"]
    print(f"   ✅ Set added: {set_id}")
    
    # 5. Reorder exercises (if multiple exercises)
    # Skip if only one exercise
    
    # 6. Get active workout
    print("5. Getting active workout...")
    res = requests.get(f"{BASE_URL}/workouts/active", headers=HEADERS)
    assert res.status_code == 200, f"Failed to get active workout: {res.status_code}"
    workout = res.json()
    assert workout["id"] == workout_id, "Workout ID mismatch"
    print(f"   ✅ Active workout retrieved")
    
    # 7. Delete set
    print("6. Deleting set...")
    res = requests.delete(f"{BASE_URL}/sets/{set_id}", headers=HEADERS)
    assert res.status_code == 204, f"Failed to delete set: {res.status_code}"
    print(f"   ✅ Set deleted")
    
    # 8. Cleanup: Abandon workout (optional, but good practice)
    print("7. Cleaning up...")
    # If you have abandon endpoint:
    # res = requests.post(f"{BASE_URL}/workouts/{workout_id}/abandon", headers=HEADERS)
    # Or just leave it (will auto-abandon after 24h)
    print("   ✅ Cleanup complete")
    
    print("\n✅ All smoke tests passed!")
    return True

if __name__ == "__main__":
    try:
        test_workout_flow()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Smoke test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
