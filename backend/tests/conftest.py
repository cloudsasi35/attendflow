"""Test configuration and fixtures."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
import os
from datetime import datetime, timezone, date
import uuid

# Set testing environment and keep OpenTelemetry exporters off during tests
os.environ["APP_ENV"] = "testing"
os.environ["OTEL_SDK_DISABLED"] = "true"

from attendflow.config import settings
from attendflow.database import get_db
from attendflow.main import app
from attendflow.models import (
    Base, User, Employee, RoleEnum, LeaveStatusEnum
)
from attendflow.security import hash_password, create_access_token


# Test database
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Create tables
Base.metadata.create_all(bind=engine)


@pytest.fixture
def db():
    """Provide a test database session."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client():
    """Provide a test client."""
    return TestClient(app)


@pytest.fixture
def admin_user(db: Session):
    """Create a test admin user."""
    user = User(
        id=uuid.uuid4(),
        email="admin@test.local",
        password_hash=hash_password("admin123"),
        role=RoleEnum.ADMIN,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user: User):
    """Create a token for admin user."""
    token, _ = create_access_token(admin_user.id, admin_user.email, admin_user.role.value)
    return token


@pytest.fixture
def employee_user(db: Session):
    """Create a test employee user."""
    user = User(
        id=uuid.uuid4(),
        email="emp@test.local",
        password_hash=hash_password("emp123"),
        role=RoleEnum.EMPLOYEE,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def employee_profile(db: Session, employee_user: User):
    """Create employee profile."""
    employee = Employee(
        id=uuid.uuid4(),
        user_id=employee_user.id,
        employee_code="EMP001",
        full_name="Test Employee",
        department="Engineering",
        job_title="Developer",
        joining_date=date(2023, 1, 1),
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@pytest.fixture
def employee_token(employee_user: User):
    """Create a token for employee user."""
    token, _ = create_access_token(employee_user.id, employee_user.email, employee_user.role.value)
    return token


@pytest.fixture
def inactive_user(db: Session):
    """Create an inactive user."""
    user = User(
        id=uuid.uuid4(),
        email="inactive@test.local",
        password_hash=hash_password("inactive123"),
        role=RoleEnum.EMPLOYEE,
        is_active=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
