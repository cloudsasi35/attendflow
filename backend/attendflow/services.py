"""Business logic services."""

from sqlalchemy.orm import Session
from datetime import date, datetime, timezone
from typing import Optional
import uuid
import pytz

from attendflow.config import settings
from attendflow.models import User, Employee, LeaveStatusEnum, RoleEnum
from attendflow.schemas import (
    EmployeeCreate, EmployeeUpdate, LeaveRequestCreate,
    EmployeeResponse, AttendanceResponse, LeaveRequestResponse,
    LeaveSummaryResponse, AdminDashboardResponse, EmployeeDashboardResponse
)
from attendflow.repositories import (
    UserRepository, EmployeeRepository, AttendanceRepository, LeaveRequestRepository
)
from attendflow.security import hash_password, verify_password


class AuthService:
    """Authentication and authorization service."""

    @staticmethod
    def create_user(
        db: Session,
        email: str,
        password: str,
        role: str,
    ) -> User:
        """Create a new user."""
        existing = UserRepository.get_by_email(db, email)
        if existing:
            raise ValueError(f"User with email {email} already exists")
        
        password_hash = hash_password(password)
        return UserRepository.create(db, email, password_hash, role)

    @staticmethod
    def verify_credentials(
        db: Session,
        email: str,
        password: str,
    ) -> Optional[User]:
        """Verify email and password."""
        user = UserRepository.get_by_email(db, email)
        if not user or not user.is_active:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user


class EmployeeService:
    """Employee management service."""

    @staticmethod
    def create_employee(
        db: Session,
        data: EmployeeCreate,
    ) -> EmployeeResponse:
        """Create a new employee with associated user."""
        # Check unique constraints
        if UserRepository.get_by_email(db, data.email):
            raise ValueError(f"Email {data.email} already in use")
        if EmployeeRepository.get_by_code(db, data.employee_code):
            raise ValueError(f"Employee code {data.employee_code} already in use")
        
        # Create user
        user = AuthService.create_user(db, data.email, data.password, "EMPLOYEE")
        
        # Create employee profile
        employee = EmployeeRepository.create(db, user.id, data)
        
        return EmployeeResponse.from_orm_data(employee, user)

    @staticmethod
    def get_employee(db: Session, employee_id: uuid.UUID) -> EmployeeResponse:
        """Get employee by ID."""
        employee = EmployeeRepository.get_by_id(db, employee_id)
        if not employee:
            raise ValueError("Employee not found")
        user = employee.user
        return EmployeeResponse.from_orm_data(employee, user)

    @staticmethod
    def list_employees(
        db: Session,
        skip: int = 0,
        limit: int = 20,
    ) -> dict:
        """List active employees."""
        employees, total = EmployeeRepository.list_active(db, skip, limit)
        items = [EmployeeResponse.from_orm_data(emp, emp.user) for emp in employees]
        return {
            "total": total,
            "page": skip // limit + 1,
            "page_size": limit,
            "items": items,
        }

    @staticmethod
    def update_employee(
        db: Session,
        employee_id: uuid.UUID,
        data: EmployeeUpdate,
    ) -> EmployeeResponse:
        """Update employee profile."""
        employee = EmployeeRepository.get_by_id(db, employee_id)
        if not employee:
            raise ValueError("Employee not found")
        
        # Check unique constraints if updating
        if data.email:
            existing = UserRepository.get_by_email(db, data.email)
            if existing and existing.id != employee.user_id:
                raise ValueError(f"Email {data.email} already in use")
        
        if data.employee_code:
            existing = EmployeeRepository.get_by_code(db, data.employee_code)
            if existing and existing.id != employee_id:
                raise ValueError(f"Employee code {data.employee_code} already in use")
        
        # Update employee
        employee = EmployeeRepository.update(db, employee, data)
        
        # Update user email if provided
        if data.email:
            employee.user.email = data.email.lower()
            db.commit()
        
        return EmployeeResponse.from_orm_data(employee, employee.user)

    @staticmethod
    def deactivate_employee(
        db: Session,
        employee_id: uuid.UUID,
    ) -> EmployeeResponse:
        """Deactivate an employee."""
        employee = EmployeeRepository.get_by_id(db, employee_id)
        if not employee:
            raise ValueError("Employee not found")
        
        # Deactivate the user account
        user = EmployeeRepository.deactivate_user(db, employee.user_id)
        
        return EmployeeResponse.from_orm_data(employee, user)


class AttendanceService:
    """Attendance tracking service."""

    @staticmethod
    def get_org_timezone():
        """Get organization timezone."""
        return pytz.timezone(settings.org_timezone)

    @staticmethod
    def get_work_date(dt: datetime) -> date:
        """Get work date in organization timezone."""
        org_tz = AttendanceService.get_org_timezone()
        local_dt = dt.astimezone(org_tz)
        return local_dt.date()

    @staticmethod
    def get_now_utc() -> datetime:
        """Get current time in UTC."""
        return datetime.now(timezone.utc)

    @staticmethod
    def check_in(db: Session, employee_id: uuid.UUID) -> AttendanceResponse:
        """Check in for today."""
        now_utc = AttendanceService.get_now_utc()
        work_date = AttendanceService.get_work_date(now_utc)
        
        # Check if already checked in
        existing = AttendanceRepository.get_today(db, employee_id, work_date)
        if existing:
            raise ValueError("Already checked in today")
        
        # Create attendance record
        record = AttendanceRepository.create_check_in(db, employee_id, work_date, now_utc)
        return AttendanceService._record_to_response(record)

    @staticmethod
    def check_out(db: Session, employee_id: uuid.UUID) -> AttendanceResponse:
        """Check out for today."""
        now_utc = AttendanceService.get_now_utc()
        work_date = AttendanceService.get_work_date(now_utc)
        
        # Get today's attendance
        record = AttendanceRepository.get_today(db, employee_id, work_date)
        if not record:
            raise ValueError("No check-in found for today")
        
        if record.check_out_at:
            raise ValueError("Already checked out today")
        
        # Check that check-out is not before check-in
        if now_utc < record.check_in_at:
            raise ValueError("Check-out time cannot be before check-in time")
        
        # Update with check-out time
        record = AttendanceRepository.update_check_out(db, record, now_utc)
        return AttendanceService._record_to_response(record)

    @staticmethod
    def get_employee_attendance_history(
        db: Session,
        employee_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> dict:
        """Get attendance history for employee."""
        records, total = AttendanceRepository.list_for_employee(db, employee_id, skip, limit)
        items = [AttendanceService._record_to_response(r) for r in records]
        return {
            "total": total,
            "page": skip // limit + 1,
            "page_size": limit,
            "items": items,
        }

    @staticmethod
    def list_attendance(
        db: Session,
        employee_id: Optional[uuid.UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> dict:
        """List all attendance records (admin)."""
        records, total = AttendanceRepository.list_all(
            db, employee_id, start_date, end_date, skip, limit
        )
        items = [AttendanceService._record_to_response(r) for r in records]
        return {
            "total": total,
            "page": skip // limit + 1,
            "page_size": limit,
            "items": items,
        }

    @staticmethod
    def get_today_summary(db: Session) -> dict:
        """Get today's attendance summary."""
        work_date = AttendanceService.get_work_date(AttendanceService.get_now_utc())
        return AttendanceRepository.count_today(db, work_date)

    @staticmethod
    def _record_to_response(record) -> AttendanceResponse:
        """Convert record to response schema."""
        return AttendanceResponse(
            id=record.id,
            employee_id=record.employee_id,
            work_date=record.work_date,
            check_in_at=record.check_in_at,
            check_out_at=record.check_out_at,
            status=record.status,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )


class LeaveService:
    """Leave request management service."""

    @staticmethod
    def request_leave(
        db: Session,
        employee_id: uuid.UUID,
        data: LeaveRequestCreate,
    ) -> LeaveRequestResponse:
        """Create a new leave request."""
        # Validate dates
        if data.end_date < data.start_date:
            raise ValueError("End date must be on or after start date")
        
        # Check for overlaps
        if LeaveRequestRepository.check_overlaps(db, employee_id, data.start_date, data.end_date):
            raise ValueError("Overlapping leave request already exists")
        
        # Create leave request
        request = LeaveRequestRepository.create(db, employee_id, data)
        return LeaveService._request_to_response(request)

    @staticmethod
    def get_employee_leave_requests(
        db: Session,
        employee_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> dict:
        """Get leave requests for employee."""
        requests, total = LeaveRequestRepository.list_for_employee(db, employee_id, skip, limit)
        items = [LeaveService._request_to_response(r) for r in requests]
        return {
            "total": total,
            "page": skip // limit + 1,
            "page_size": limit,
            "items": items,
        }

    @staticmethod
    def list_leave_requests(
        db: Session,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> dict:
        """List all leave requests (admin)."""
        status_enum = None
        if status:
            status_enum = LeaveStatusEnum[status.upper()]
        
        requests, total = LeaveRequestRepository.list_all(db, status_enum, skip, limit)
        items = [LeaveService._request_to_response(r) for r in requests]
        return {
            "total": total,
            "page": skip // limit + 1,
            "page_size": limit,
            "items": items,
        }

    @staticmethod
    def approve_leave(
        db: Session,
        request_id: uuid.UUID,
        approved_by_user_id: uuid.UUID,
        decision_note: Optional[str] = None,
    ) -> LeaveRequestResponse:
        """Approve a leave request."""
        request = LeaveRequestRepository.get_by_id(db, request_id)
        if not request:
            raise ValueError("Leave request not found")
        
        if request.status != LeaveStatusEnum.PENDING:
            raise ValueError("Only pending requests can be approved")
        
        request = LeaveRequestRepository.approve(db, request, approved_by_user_id, decision_note)
        return LeaveService._request_to_response(request)

    @staticmethod
    def reject_leave(
        db: Session,
        request_id: uuid.UUID,
        rejected_by_user_id: uuid.UUID,
        decision_note: Optional[str] = None,
    ) -> LeaveRequestResponse:
        """Reject a leave request."""
        request = LeaveRequestRepository.get_by_id(db, request_id)
        if not request:
            raise ValueError("Leave request not found")
        
        if request.status != LeaveStatusEnum.PENDING:
            raise ValueError("Only pending requests can be rejected")
        
        request = LeaveRequestRepository.reject(db, request, rejected_by_user_id, decision_note)
        return LeaveService._request_to_response(request)

    @staticmethod
    def get_leave_summary(db: Session, employee_id: uuid.UUID) -> LeaveSummaryResponse:
        """Get leave summary for employee."""
        approved = LeaveRequestRepository.count_approved_for_employee(db, employee_id)
        pending = LeaveRequestRepository.count_pending_for_employee(db, employee_id)
        rejected = LeaveRequestRepository.count_rejected_for_employee(db, employee_id)
        return LeaveSummaryResponse(
            approved_days=approved,
            pending_days=pending,
            rejected_days=rejected,
        )

    @staticmethod
    def _request_to_response(request) -> LeaveRequestResponse:
        """Convert request to response schema."""
        return LeaveRequestResponse(
            id=request.id,
            employee_id=request.employee_id,
            leave_type=request.leave_type,
            start_date=request.start_date,
            end_date=request.end_date,
            reason=request.reason,
            status=request.status,
            decision_note=request.decision_note,
            decided_by_user_id=request.decided_by_user_id,
            decided_at=request.decided_at,
            created_at=request.created_at,
            updated_at=request.updated_at,
        )


class DashboardService:
    """Dashboard and reporting service."""

    @staticmethod
    def get_admin_dashboard(db: Session) -> AdminDashboardResponse:
        """Get admin dashboard."""
        from attendflow.models import User
        
        # Count active employees
        active_employees = db.query(User).filter(User.is_active == True, User.role == RoleEnum.EMPLOYEE).count()
        
        # Get today's summary
        work_date = AttendanceService.get_work_date(AttendanceService.get_now_utc())
        today_summary = AttendanceRepository.count_today(db, work_date)
        
        # Get pending leave requests
        pending_count = LeaveRequestRepository.count_pending(db)
        
        # Get recent attendance
        recent_attendance = AttendanceRepository.get_recent_attendance(db, work_date, limit=5)
        attendance_items = [AttendanceService._record_to_response(r) for r in recent_attendance]
        
        # Get pending leave requests list
        pending_leaves, _ = LeaveRequestRepository.list_all(db, LeaveStatusEnum.PENDING, 0, 5)
        leave_items = [LeaveService._request_to_response(r) for r in pending_leaves]
        
        return AdminDashboardResponse(
            active_employees=active_employees,
            present_today=today_summary["present_today"],
            incomplete_today=today_summary["incomplete_today"],
            pending_leave_requests=pending_count,
            recent_attendance=attendance_items,
            pending_leave_requests_list=leave_items,
        )

    @staticmethod
    def get_employee_dashboard(
        db: Session,
        employee_id: uuid.UUID,
    ) -> EmployeeDashboardResponse:
        """Get employee dashboard."""
        # Get today's attendance
        work_date = AttendanceService.get_work_date(AttendanceService.get_now_utc())
        today_record = AttendanceRepository.get_today(db, employee_id, work_date)
        
        today_status = None
        if today_record:
            today_status = AttendanceService._record_to_response(today_record)
        
        today_absent = today_record is None
        
        # Get recent attendance
        recent, _ = AttendanceRepository.list_for_employee(db, employee_id, 0, 5)
        recent_items = [AttendanceService._record_to_response(r) for r in recent]
        
        # Get leave summary
        leave_summary = LeaveService.get_leave_summary(db, employee_id)
        
        # Get recent leave requests
        recent_leaves, _ = LeaveRequestRepository.list_for_employee(db, employee_id, 0, 5)
        leave_items = [LeaveService._request_to_response(r) for r in recent_leaves]
        
        return EmployeeDashboardResponse(
            today_status=today_status,
            today_absent=today_absent,
            recent_attendance=recent_items,
            leave_summary=leave_summary,
            recent_leave_requests=leave_items,
        )
