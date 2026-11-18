"""Health check API routes."""

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from attendflow.database import get_db

logger = logging.getLogger(__name__)

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
    except Exception:
        logger.exception("Readiness check failed: database unavailable")
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "unavailable"},
        )
