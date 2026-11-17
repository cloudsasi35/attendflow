"""Seed demo data for development."""

import os
import sys
from datetime import datetime, timedelta, timezone, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from attendflow.config import settings
from attendflow.models import (
    User, Employee, AttendanceRecord, LeaveRequest, Base,
    RoleEnum, LeaveTypeEnum, LeaveStatusEnum
)
from attendflow.security import hash_password
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check environment
if settings.app_env == "production":
    logger.error("❌ Cannot seed demo data in production!")
    sys.exit(1)

# Create engine
engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
logger.info("Creating database tables...")
Base.metadata.create_all(bind=engine)

# Clear existing data
logger.info("Clearing existing seed data...")
db = SessionLocal()
db.query(LeaveRequest).delete()
db.query(AttendanceRecord).delete()
db.query(Employee).delete()
db.query(User).delete()
db.commit()

# Create admin user
logger.info("Creating admin user...")
admin_user = User(
    id=uuid.uuid4(),
    email="admin@attendflow.local",
    password_hash=hash_password("admin123"),
    role=RoleEnum.ADMIN,
    is_active=True,
)
db.add(admin_user)
db.flush()

# Create employee users and profiles
logger.info("Creating demo employees...")
employees_data = [
    {
        "email": "alice.kumar@attendflow.local",
        "name": "Alice Kumar (Demo)",
        "code": "EMP001",
        "dept": "Engineering",
        "title": "Senior Developer",
    },
    {
        "email": "bob.sharma@attendflow.local",
        "name": "Bob Sharma (Demo)",
        "code": "EMP002",
        "dept": "Sales",
        "title": "Sales Manager",
    },
    {
        "email": "carol.patel@attendflow.local",
        "name": "Carol Patel (Demo)",
        "code": "EMP003",
        "dept": "HR",
        "title": "HR Specialist",
    },
]

employees = []
for emp_data in employees_data:
    emp_user = User(
        id=uuid.uuid4(),
        email=emp_data["email"],
        password_hash=hash_password("employee123"),
        role=RoleEnum.EMPLOYEE,
        is_active=True,
    )
    db.add(emp_user)
    db.flush()

    employee = Employee(
        id=uuid.uuid4(),
        user_id=emp_user.id,
        employee_code=emp_data["code"],
        full_name=emp_data["name"],
        department=emp_data["dept"],
        job_title=emp_data["title"],
        joining_date=date(2023, 1, 15),
    )
    db.add(employee)
    db.flush()
    employees.append(employee)

# Create attendance records for recent days
logger.info("Creating attendance records...")
now_utc = datetime.now(timezone.utc)
org_tz_name = settings.org_timezone
import pytz
org_tz = pytz.timezone(org_tz_name)

# Get work date in org timezone
local_now = now_utc.astimezone(org_tz)
today_work_date = local_now.date()

# Last 5 work days (excluding weekends)
for i in range(10):
    check_date = today_work_date - timedelta(days=i)
    
    # Skip weekends
    if check_date.weekday() >= 5:
        continue

    for emp in employees[:2]:  # Only first 2 employees have attendance
        # Random check-in time between 8-10 AM
        check_in_hour = 8 + (i % 2)
        check_in_time = org_tz.localize(
            datetime.combine(check_date, datetime.min.time().replace(hour=check_in_hour, minute=30))
        ).astimezone(timezone.utc)

        # Check-out time 5-6 PM (most have checked out)
        check_out_hour = 17 + (i % 1)
        check_out_time = org_tz.localize(
            datetime.combine(check_date, datetime.min.time().replace(hour=check_out_hour, minute=0))
        ).astimezone(timezone.utc)

        # One record today with no check-out
        if check_date == today_work_date and emp == employees[0]:
            check_out_time = None

        record = AttendanceRecord(
            id=uuid.uuid4(),
            employee_id=emp.id,
            work_date=check_date,
            check_in_at=check_in_time,
            check_out_at=check_out_time,
        )
        db.add(record)

# Create leave requests
logger.info("Creating leave requests...")
# Pending leave request
pending_leave = LeaveRequest(
    id=uuid.uuid4(),
    employee_id=employees[0].id,
    leave_type=LeaveTypeEnum.CASUAL,
    start_date=today_work_date + timedelta(days=7),
    end_date=today_work_date + timedelta(days=9),
    reason="(Demo) Planned vacation",
    status=LeaveStatusEnum.PENDING,
)
db.add(pending_leave)

# Approved leave request
approved_leave = LeaveRequest(
    id=uuid.uuid4(),
    employee_id=employees[1].id,
    leave_type=LeaveTypeEnum.SICK,
    start_date=today_work_date - timedelta(days=5),
    end_date=today_work_date - timedelta(days=4),
    reason="(Demo) Medical appointment",
    status=LeaveStatusEnum.APPROVED,
    decided_by_user_id=admin_user.id,
    decided_at=datetime.now(timezone.utc),
    decision_note="(Demo) Approved",
)
db.add(approved_leave)

# Rejected leave request
rejected_leave = LeaveRequest(
    id=uuid.uuid4(),
    employee_id=employees[2].id,
    leave_type=LeaveTypeEnum.UNPAID,
    start_date=today_work_date - timedelta(days=10),
    end_date=today_work_date - timedelta(days=8),
    reason="(Demo) Personal reasons",
    status=LeaveStatusEnum.REJECTED,
    decided_by_user_id=admin_user.id,
    decided_at=datetime.now(timezone.utc),
    decision_note="(Demo) Not approved at this time",
)
db.add(rejected_leave)

# Commit all
db.commit()
db.close()

logger.info("✅ Demo data seeded successfully!")
logger.info("\nDemo Credentials:")
logger.info("  Admin:    admin@attendflow.local / admin123")
logger.info("  Employee: alice.kumar@attendflow.local / employee123")
logger.info("  Employee: bob.sharma@attendflow.local / employee123")
logger.info("  Employee: carol.patel@attendflow.local / employee123")
