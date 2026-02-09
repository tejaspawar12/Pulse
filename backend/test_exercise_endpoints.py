"""
Test script for exercise endpoints (Week 2 Day 1).
Tests GET /exercises and GET /exercises/recent endpoints.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.config.database import SessionLocal
from app.models.user import User
from app.utils.enums import LifecycleStatus, CompletionStatus
import uuid

# Test user ID (should match your test user)
TEST_USER_ID = "6b02afa2-2fe6-4140-9745-851c4bc0613f"

client = TestClient(app)
headers = {"X-DEV-USER-ID": TEST_USER_ID}

print("🧪 Testing Exercise Endpoints (Week 2 Day 1)\n")

# Test 1: Search exercises with query
print("1. Testing GET /exercises?q=bench...")
response = client.get("/api/v1/exercises", params={"q": "bench"}, headers=headers)
assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
data = response.json()
assert "exercises" in data, "Response should have 'exercises' key"
assert len(data["exercises"]) > 0, "Should return at least one exercise for 'bench'"
print(f"   ✅ Found {len(data['exercises'])} exercises")
for ex in data["exercises"][:3]:
    print(f"      - {ex['name']} ({ex['primary_muscle_group']}, {ex['equipment']})")

# Test 2: Search with query too short
print("\n2. Testing GET /exercises?q=b (too short)...")
response = client.get("/api/v1/exercises", params={"q": "b"}, headers=headers)
assert response.status_code == 200, f"Expected 200, got {response.status_code}"
data = response.json()
assert len(data["exercises"]) == 0, "Should return empty list for query < 2 chars"
print("   ✅ Returns empty list (query too short)")

# Test 3: Search with muscle group filter
print("\n3. Testing GET /exercises?muscle_group=chest...")
response = client.get("/api/v1/exercises", params={"muscle_group": "chest"}, headers=headers)
assert response.status_code == 200, f"Expected 200, got {response.status_code}"
data = response.json()
assert len(data["exercises"]) > 0, "Should return chest exercises"
all_chest = all(ex["primary_muscle_group"] == "chest" for ex in data["exercises"])
assert all_chest, "All exercises should be chest"
print(f"   ✅ Found {len(data['exercises'])} chest exercises")

# Test 4: Search with equipment filter
print("\n4. Testing GET /exercises?equipment=barbell...")
response = client.get("/api/v1/exercises", params={"equipment": "barbell"}, headers=headers)
assert response.status_code == 200, f"Expected 200, got {response.status_code}"
data = response.json()
assert len(data["exercises"]) > 0, "Should return barbell exercises"
all_barbell = all(ex["equipment"] == "barbell" for ex in data["exercises"])
assert all_barbell, "All exercises should be barbell"
print(f"   ✅ Found {len(data['exercises'])} barbell exercises")

# Test 5: Search with combined filters
print("\n5. Testing GET /exercises?q=press&muscle_group=chest...")
response = client.get(
    "/api/v1/exercises",
    params={"q": "press", "muscle_group": "chest"},
    headers=headers
)
assert response.status_code == 200, f"Expected 200, got {response.status_code}"
data = response.json()
print(f"   ✅ Found {len(data['exercises'])} exercises matching 'press' and chest")

# Test 6: Recent exercises
print("\n6. Testing GET /exercises/recent...")
response = client.get("/api/v1/exercises/recent", headers=headers)
assert response.status_code == 200, f"Expected 200, got {response.status_code}"
data = response.json()
assert "exercises" in data, "Response should have 'exercises' key"
print(f"   ✅ Found {len(data['exercises'])} recent exercises")
if len(data["exercises"]) > 0:
    for ex in data["exercises"][:3]:
        print(f"      - {ex['name']}")
else:
    print("      (No recent exercises - user hasn't completed any workouts yet)")

print("\n🎉 All exercise endpoint tests passed!")
