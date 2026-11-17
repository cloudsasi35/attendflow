"""SQLAlchemy models for AttendFlow."""

from sqlalchemy import Column, String, Boolean, DateTime, Date, ForeignKey, Enum, Text, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

Base = declarative_base()


class RoleEnum(str, enum.Enum):
    """User role enumeration."""
    ADMIN = "ADMIN"
    EMPLOYEE = "EMPLOYEE"


class LeaveTypeEnum(str, enum.Enum):
    """Leave type enumeration."""
    CASUAL = "CASUAL"
    SICK = "SICK"
    UNPAID = "UNPAID"


class LeaveStatusEnum(str, enum.Enum):
    """Leave request status enumeration."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.EMPLOYEE)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    employee = relationship("Employee", back_populates="user", uselist=False, cascade="all, delete-orphan")
    decided_leave_requests = relationship("LeaveRequest", foreign_keys="LeaveRequest.decided_by_user_id", back_populates="decided_by_user")

    def __repr__(self):
        return f"<User {self.email}>"


class Employee(Base):
    """Employee model for employee profile."""
    __tablename__ = "employees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    employee_code = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    department = Column(String(255), nullable=True)
    job_title = Column(String(255), nullable=True)
    joining_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="employee")
    attendance_records = relationship("AttendanceRecord", back_populates="employee", cascade="all, delete-orphan")
    leave_requests = relationship("LeaveRequest", back_populates="employee", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Employee {self.employee_code} - {self.full_name}>"


class AttendanceRecord(Base):
    """Attendance record for daily check-in/check-out."""
    __tablename__ = "attendance_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False, index=True)
    work_date = Column(Date, nullable=False)  # Local date in organization timezone
    check_in_at = Column(DateTime(timezone=True), nullable=False)  # UTC timestamp
    check_out_at = Column(DateTime(timezone=True), nullable=True)  # UTC timestamp or NULL
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Unique constraint on (employee_id, work_date) - one record per day per employee
    __table_args__ = (
        UniqueConstraint("employee_id", "work_date", name="uq_employee_workdate"),
        Index("idx_work_date", "work_date"),
        Index("idx_employee_workdate", "employee_id", "work_date"),
    )

    # Relationships
    employee = relationship("Employee", back_populates="attendance_records")

    def __repr__(self):
        return f"<AttendanceRecord {self.employee_id} on {self.work_date}>"

    @property
    def status(self):
        """Derive status from check-out timestamp."""
        if self.check_out_at is None:
            return "INCOMPLETE"
        return "PRESENT"


class LeaveRequest(Base):
    """Leave request model."""
    __tablename__ = "leave_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False, index=True)
    leave_type = Column(Enum(LeaveTypeEnum), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(Enum(LeaveStatusEnum), nullable=False, default=LeaveStatusEnum.PENDING)
    decision_note = Column(Text, nullable=True)
    decided_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_employee_status", "employee_id", "status"),
        Index("idx_status_startdate", "status", "start_date"),
    )

    # Relationships
    employee = relationship("Employee", back_populates="leave_requests")
    decided_by_user = relationship("User", foreign_keys=[decided_by_user_id], back_populates="decided_leave_requests")

    def __repr__(self):
        return f"<LeaveRequest {self.employee_id} {self.start_date} to {self.end_date}>"
