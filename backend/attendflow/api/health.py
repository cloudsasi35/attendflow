"""Health check API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from attendflow.database import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def health_live():
    """Liveness probe: application is running."""
    return {"status": "ok"}


@router.get("/ready")
async def health_ready(db: Session = Depends(get_db)):
    """Readiness probe: application and database are ready."""
    try:
        # Try a simple database query
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}, 503
