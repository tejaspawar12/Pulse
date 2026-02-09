"""
Server time endpoint (optional, not used in Phase 1 timer logic).
"""
from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter()


@router.get("/time")
def get_server_time():
    """
    Get server time in ISO format.
    No auth required.
    
    Note: Timer does NOT depend on this in Phase 1.
    Available for future use.
    """
    return {
        "server_time": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    }
