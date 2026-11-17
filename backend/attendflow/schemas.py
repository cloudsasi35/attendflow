"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime
from typing import Optional
from enum import Enum
import uuid
import re


# ========== Enums ==========
class RoleEnum(str, Enum):
    ADMIN = "ADMIN"
    EMPLOYEE = "EMPLOYEE"


class LeaveTypeEnum(str, Enum):
    CASUAL = "CASUAL"
    SICK = "SICK"
    UNPAID = "UNPAID"


class LeaveStatusEnum(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# ========== Email Validation ==========
def validate_email(email: str) -> str:
    """Simple email validation allowing .local domains."""
    if not email or not isinstance(email, str):
        raise ValueError("Email must be a non-empty string")
    if len(email) > 255 or len(email) < 3:
        raise ValueError("Email must be between 3 and 255 characters")
    # Simple regex pattern that allows .local and other domains
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z0-9]{2,}$'
    if not re.match(pattern, email):
        raise ValueError("Invalid email format")
    return email


# ========== Auth ==========
class UserLogin(BaseModel):
    """Login request."""
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=255)

    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        return validate_email(v)


class UserResponse(BaseModel):
    """User response (no password hash)."""
    id: uuid.UUID
    email: str
    role: RoleEnum
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """Authentication response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ========== Employee ==========
class EmployeeCreate(BaseModel):
    """Create employee request."""
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=255)
    employee_code: str = Field(min_length=1, max_length=50)
    full_name: str = Field(min_length=1, max_length=255)
    department: Optional[str] = Field(None, max_length=255)
    job_title: Optional[str] = Field(None, max_length=255)
    joining_date: date

    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        return validate_email(v)


class EmployeeUpdate(BaseModel):
    """Update employee request."""
    email: Optional[str] = Field(None, min_length=3, max_length=255)
    employee_code: Optional[str] = Field(None, min_length=1, max_length=50)
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    department: Optional[str] = Field(None, max_length=255)
    job_title: Optional[str] = Field(None, max_length=255)
    joining_date: Optional[date] = None

    @field_validator('email', mode='before')
    @classmethod
    def validate_email_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return validate_email(v)



class EmployeeResponse(BaseModel):
    """Employee response."""
    id: uuid.UUID
    user_id: uuid.UUID
    email: str
    role: RoleEnum
    is_active: bool
    employee_code: str
    full_name: str
    department: Optional[str]
    job_title: Optional[str]
    joining_date: date
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def from_orm_data(employee, user):
        """Construct from ORM models."""
        return EmployeeResponse(
            id=employee.id,
            user_id=user.id,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            employee_code=employee.employee_code,
            full_name=employee.full_name,
            department=employee.department,
            job_title=employee.job_title,
            joining_date=employee.joining_date,
            created_at=employee.created_at,
            updated_at=employee.updated_at,
        )

    class Config:
        from_attributes = True


class EmployeeListResponse(BaseModel):
    """List employees response."""
    total: int
    page: int
    page_size: int
    items: list[EmployeeResponse]


# ========== Attendance ==========
class AttendanceCheckIn(BaseModel):
    """Check-in request."""
    pass  # No fields; uses current time


class AttendanceCheckOut(BaseModel):
    """Check-out request."""
    pass  # No fields; uses current time


class AttendanceResponse(BaseModel):
    """Attendance response."""
    id: uuid.UUID
    employee_id: uuid.UUID
    work_date: date
    check_in_at: datetime
    check_out_at: Optional[datetime]
    status: str  # "PRESENT" or "INCOMPLETE"
    created_at: datetime
    updated_at: datetime

    @property
    def computed_status(self):
        return "INCOMPLETE" if self.check_out_at is None else "PRESENT"

    class Config:
        from_attributes = True


class AttendanceListResponse(BaseModel):
    """List attendance response."""
    total: int
    page: int
    page_size: int
    items: list[AttendanceResponse]


class AttendanceTodayResponse(BaseModel):
    """Today's attendance summary for admin."""
    total_employees: int
    present_today: int
    incomplete_today: int
    absent_today: int


# ========== Leave ==========
class LeaveRequestCreate(BaseModel):
    """Create leave request."""
    leave_type: LeaveTypeEnum
    start_date: date
    end_date: date
    reason: str = Field(min_length=1, max_length=1000)

    @field_validator("end_date")
    @classmethod
    def end_date_after_start(cls, v, info):
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("end_date must be >= start_date")
        return v


class LeaveRequestApprove(BaseModel):
    """Approve leave request."""
    decision_note: Optional[str] = Field(None, max_length=1000)


class LeaveRequestReject(BaseModel):
    """Reject leave request."""
    decision_note: Optional[str] = Field(None, max_length=1000)


class LeaveRequestResponse(BaseModel):
    """Leave request response."""
    id: uuid.UUID
    employee_id: uuid.UUID
    leave_type: LeaveTypeEnum
    start_date: date
    end_date: date
    reason: str
    status: LeaveStatusEnum
    decision_note: Optional[str]
    decided_by_user_id: Optional[uuid.UUID]
    decided_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LeaveRequestListResponse(BaseModel):
    """List leave requests response."""
    total: int
    page: int
    page_size: int
    items: list[LeaveRequestResponse]


class LeaveSummaryResponse(BaseModel):
    """Leave summary for employee."""
    approved_days: int
    pending_days: int
    rejected_days: int


# ========== Dashboard ==========
class AdminDashboardResponse(BaseModel):
    """Admin dashboard metrics."""
    active_employees: int
    present_today: int
    incomplete_today: int
    pending_leave_requests: int
    recent_attendance: list[AttendanceResponse]
    pending_leave_requests_list: list[LeaveRequestResponse]


class EmployeeDashboardResponse(BaseModel):
    """Employee dashboard."""
    today_status: Optional[AttendanceResponse]
    today_absent: bool
    recent_attendance: list[AttendanceResponse]
    leave_summary: LeaveSummaryResponse
    recent_leave_requests: list[LeaveRequestResponse]


# ========== Reports ==========
class AttendanceReportResponse(BaseModel):
    """Attendance report."""
    total: int
    page: int
    page_size: int
    items: list[AttendanceResponse]


class LeaveReportResponse(BaseModel):
    """Leave report."""
    total: int
    page: int
    page_size: int
    items: list[LeaveRequestResponse]


# ========== Errors ==========
class ErrorResponse(BaseModel):
    """Error response."""
    detail: str
