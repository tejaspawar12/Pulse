"""
Health check endpoint.
"""
from fastapi import APIRouter
from sqlalchemy import text
from app.config.database import engine

router = APIRouter()


@router.get("/health")
def health_check():
    """
    Health check endpoint.
    Returns database connection status.
    No auth required.
    """
    try:
        # Test database connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "error",
            "database": "disconnected",
            "error": str(e)
        }
