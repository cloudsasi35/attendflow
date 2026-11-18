"""FastAPI application factory and configuration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from attendflow.config import settings
from attendflow.telemetry import configure_telemetry, instrument_fastapi

logger = logging.getLogger(__name__)

configure_telemetry()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description="Employee Attendance & Leave Management API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    instrument_fastapi(app)

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    from attendflow.api import auth, employees, attendance, leave, dashboard, health

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(employees.router)
    app.include_router(attendance.router)
    app.include_router(leave.router)
    app.include_router(dashboard.router)

    logger.info(f"AttendFlow API started (env={settings.app_env})")

    return app


app = create_app()
