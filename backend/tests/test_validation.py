"""
Integration tests for input validation.
"""
import pytest
from fastapi import status

def test_invalid_uuid_returns_422(client, auth_headers):
    """
    Test that invalid UUID format returns 422 (validation error).
    
    ⚠️ LOCKED: FastAPI returns 422 for invalid UUID path params by default.
    Only use 400 if you've implemented custom parsing/exception handling.
    """
    # Test invalid UUID in various endpoints
    # Set endpoint (PATCH - endpoint exists)
    response = client.patch(
        "/api/v1/sets/not-a-uuid",
        json={"reps": 10},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # Workout endpoint (POST - endpoint exists)
    response = client.post(
        "/api/v1/workouts/not-a-uuid/exercises",
        json={"exercise_id": "00000000-0000-0000-0000-000000000000"},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # Exercise reorder endpoint
    response = client.patch(
        "/api/v1/workouts/not-a-uuid/exercises/reorder",
        json={"items": []},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
