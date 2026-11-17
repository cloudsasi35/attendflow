"""Database setup and utilities."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import logging
from attendflow.config import settings

logger = logging.getLogger(__name__)

# Create engine with appropriate pooling for the environment
if settings.app_env == "testing":
    engine = create_engine(
        settings.database_url,
        echo=False,
        poolclass=NullPool,
    )
else:
    engine = create_engine(
        settings.database_url,
        echo=settings.debug,
        pool_size=10,
        max_overflow=20,
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Session:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database (create tables if not exist)."""
    # Import all models to ensure they're registered
    from attendflow.models import User, Employee, AttendanceRecord, LeaveRequest
    
    # Create all tables
    from attendflow.models import Base
    Base.metadata.create_all(bind=engine)
