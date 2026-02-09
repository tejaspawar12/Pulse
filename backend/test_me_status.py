"""
Test for GET /me/status endpoint.
Verifies:
- Returns 200 status
- JSON contains proper boolean values (true/false, not strings)
- Schema validation
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


def test_me_status_returns_200():
    """Test that /me/status returns 200 with proper structure."""
    # Create a test user
    db = SessionLocal()
    try:
        test_user = User(
            id=uuid.uuid4(),
            email=f"test_{uuid.uuid4().hex[:8]}@example.com",
            password_hash="dummy_hash",
            units="kg",
            timezone="Asia/Kolkata",
            default_rest_timer_seconds=90
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        # Test endpoint
        headers = {"X-DEV-USER-ID": str(test_user.id)}
        response = client.get("/api/v1/me/status", headers=headers)
        
        # Verify status code
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify response structure
        data = response.json()
        assert "active_workout" in data
        assert "today_worked_out" in data
        assert "last_30_days" in data
        
        # CRITICAL: Verify today_worked_out is boolean (not string)
        assert isinstance(data["today_worked_out"], bool), \
            f"today_worked_out must be bool, got {type(data['today_worked_out'])}: {data['today_worked_out']}"
        assert data["today_worked_out"] in (True, False), \
            f"today_worked_out must be True or False, got: {data['today_worked_out']}"
        
        # CRITICAL: Verify last_30_days contains proper booleans
        assert isinstance(data["last_30_days"], list)
        assert len(data["last_30_days"]) == 30, f"Expected 30 days, got {len(data['last_30_days'])}"
        
        for day in data["last_30_days"]:
            assert "date" in day
            assert "worked_out" in day
            # CRITICAL: Verify worked_out is boolean (not string)
            assert isinstance(day["worked_out"], bool), \
                f"worked_out must be bool, got {type(day['worked_out'])}: {day['worked_out']}"
            assert day["worked_out"] in (True, False), \
                f"worked_out must be True or False, got: {day['worked_out']}"
        
        print("✅ /me/status returns 200")
        print(f"✅ today_worked_out is proper bool: {data['today_worked_out']} (type: {type(data['today_worked_out'])})")
        print(f"✅ last_30_days has {len(data['last_30_days'])} days with proper bool values")
        print(f"✅ Sample day: {data['last_30_days'][0]}")
        
        # Cleanup
        db.delete(test_user)
        db.commit()
        
    finally:
        db.close()


if __name__ == "__main__":
    print("Testing GET /api/v1/me/status endpoint...")
    test_me_status_returns_200()
    print("\n🎉 All /me/status tests passed!")
