"""Repository layer for database operations."""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from datetime import date, datetime
from typing import Optional
import uuid

from attendflow.models import (
    User, Employee, AttendanceRecord, LeaveRequest,
    RoleEnum, LeaveStatusEnum, LeaveTypeEnum
)
from attendflow.schemas import (
    EmployeeCreate, EmployeeUpdate, AttendanceCheckIn, AttendanceCheckOut,
    LeaveRequestCreate
)


class UserRepository:
    """Repository for User operations."""

    @staticmethod
    def get_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email.lower()).first()

    @staticmethod
    def create(db: Session, email: str, password_hash: str, role: RoleEnum) -> User:
        user = User(email=email.lower(), password_hash=password_hash, role=role, is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


class EmployeeRepository:
    """Repository for Employee operations."""

    @staticmethod
    def get_by_id(db: Session, employee_id: uuid.UUID) -> Optional[Employee]:
        return db.query(Employee).filter(Employee.id == employee_id).first()

    @staticmethod
    def get_by_user_id(db: Session, user_id: uuid.UUID) -> Optional[Employee]:
        return db.query(Employee).filter(Employee.user_id == user_id).first()

    @staticmethod
    def get_by_code(db: Session, employee_code: str) -> Optional[Employee]:
        return db.query(Employee).filter(Employee.employee_code == employee_code).first()

    @staticmethod
    def list_active(
        db: Session,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Employee], int]:
        """List active employees with pagination."""
        query = db.query(Employee).join(User).filter(User.is_active == True)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    @staticmethod
    def create(db: Session, user_id: uuid.UUID, data: EmployeeCreate) -> Employee:
        employee = Employee(
            user_id=user_id,
            employee_code=data.employee_code,
            full_name=data.full_name,
            department=data.department,
            job_title=data.job_title,
            joining_date=data.joining_date,
        )
        db.add(employee)
        db.commit()
        db.refresh(employee)
        return employee

    @staticmethod
    def update(db: Session, employee: Employee, data: EmployeeUpdate) -> Employee:
        """Update employee fields."""
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(employee, field):
                setattr(employee, field, value)
        db.commit()
        db.refresh(employee)
        return employee

    @staticmethod
    def deactivate_user(db: Session, user_id: uuid.UUID) -> User:
        """Deactivate a user (employee cannot log in)."""
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.is_active = False
            db.commit()
            db.refresh(user)
        return user


class AttendanceRepository:
    """Repository for AttendanceRecord operations."""

    @staticmethod
    def get_by_id(db: Session, record_id: uuid.UUID) -> Optional[AttendanceRecord]:
        return db.query(AttendanceRecord).filter(AttendanceRecord.id == record_id).first()

    @staticmethod
    def get_today(db: Session, employee_id: uuid.UUID, work_date: date) -> Optional[AttendanceRecord]:
        """Get today's attendance record for an employee."""
        return db.query(AttendanceRecord).filter(
            and_(
                AttendanceRecord.employee_id == employee_id,
                AttendanceRecord.work_date == work_date,
            )
        ).first()

    @staticmethod
    def create_check_in(
        db: Session,
        employee_id: uuid.UUID,
        work_date: date,
        check_in_at: datetime,
    ) -> AttendanceRecord:
        """Create a new attendance record with check-in."""
        record = AttendanceRecord(
            employee_id=employee_id,
            work_date=work_date,
            check_in_at=check_in_at,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def update_check_out(
        db: Session,
        record: AttendanceRecord,
        check_out_at: datetime,
    ) -> AttendanceRecord:
        """Update check-out time."""
        record.check_out_at = check_out_at
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def list_for_employee(
        db: Session,
        employee_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[AttendanceRecord], int]:
        """List attendance records for an employee."""
        query = db.query(AttendanceRecord).filter(
            AttendanceRecord.employee_id == employee_id
        ).order_by(desc(AttendanceRecord.work_date))
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    @staticmethod
    def list_all(
        db: Session,
        employee_id: Optional[uuid.UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[AttendanceRecord], int]:
        """List all attendance records with optional filters."""
        query = db.query(AttendanceRecord)

        if employee_id:
            query = query.filter(AttendanceRecord.employee_id == employee_id)
        if start_date:
            query = query.filter(AttendanceRecord.work_date >= start_date)
        if end_date:
            query = query.filter(AttendanceRecord.work_date <= end_date)

        total = query.count()
        items = query.order_by(desc(AttendanceRecord.work_date)).offset(skip).limit(limit).all()
        return items, total

    @staticmethod
    def count_today(db: Session, work_date: date) -> dict:
        """Count today's attendance statistics."""
        total = db.query(func.count(Employee.id)).filter(
            Employee.user.has(User.is_active == True)
        ).scalar() or 0

        present = db.query(func.count(AttendanceRecord.id)).filter(
            and_(
                AttendanceRecord.work_date == work_date,
                AttendanceRecord.check_out_at.isnot(None),
            )
        ).scalar() or 0

        incomplete = db.query(func.count(AttendanceRecord.id)).filter(
            and_(
                AttendanceRecord.work_date == work_date,
                AttendanceRecord.check_out_at.is_(None),
            )
        ).scalar() or 0

        absent = total - present - incomplete

        return {
            "total_employees": total,
            "present_today": present,
            "incomplete_today": incomplete,
            "absent_today": absent,
        }

    @staticmethod
    def get_recent_attendance(
        db: Session,
        work_date: date,
        limit: int = 10,
    ) -> list[AttendanceRecord]:
        """Get recent attendance records for today."""
        return db.query(AttendanceRecord).filter(
            AttendanceRecord.work_date == work_date
        ).order_by(desc(AttendanceRecord.check_in_at)).limit(limit).all()


class LeaveRequestRepository:
    """Repository for LeaveRequest operations."""

    @staticmethod
    def get_by_id(db: Session, request_id: uuid.UUID) -> Optional[LeaveRequest]:
        return db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()

    @staticmethod
    def create(
        db: Session,
        employee_id: uuid.UUID,
        data: LeaveRequestCreate,
    ) -> LeaveRequest:
        """Create a new leave request."""
        request = LeaveRequest(
            employee_id=employee_id,
            leave_type=data.leave_type,
            start_date=data.start_date,
            end_date=data.end_date,
            reason=data.reason,
            status=LeaveStatusEnum.PENDING,
        )
        db.add(request)
        db.commit()
        db.refresh(request)
        return request

    @staticmethod
    def list_for_employee(
        db: Session,
        employee_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[LeaveRequest], int]:
        """List leave requests for an employee."""
        query = db.query(LeaveRequest).filter(
            LeaveRequest.employee_id == employee_id
        ).order_by(desc(LeaveRequest.created_at))
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    @staticmethod
    def list_all(
        db: Session,
        status: Optional[LeaveStatusEnum] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[LeaveRequest], int]:
        """List all leave requests with optional status filter."""
        query = db.query(LeaveRequest)
        if status:
            query = query.filter(LeaveRequest.status == status)
        
        total = query.count()
        items = query.order_by(
            desc(LeaveRequest.status == LeaveStatusEnum.PENDING),
            desc(LeaveRequest.created_at),
        ).offset(skip).limit(limit).all()
        return items, total

    @staticmethod
    def check_overlaps(
        db: Session,
        employee_id: uuid.UUID,
        start_date: date,
        end_date: date,
        exclude_request_id: Optional[uuid.UUID] = None,
    ) -> bool:
        """Check if there are overlapping PENDING or APPROVED leaves."""
        query = db.query(LeaveRequest).filter(
            and_(
                LeaveRequest.employee_id == employee_id,
                or_(
                    LeaveRequest.status == LeaveStatusEnum.PENDING,
                    LeaveRequest.status == LeaveStatusEnum.APPROVED,
                ),
                # Overlap: not (end1 < start2 or start1 > end2)
                LeaveRequest.end_date >= start_date,
                LeaveRequest.start_date <= end_date,
            )
        )
        if exclude_request_id:
            query = query.filter(LeaveRequest.id != exclude_request_id)
        return query.first() is not None

    @staticmethod
    def approve(
        db: Session,
        request: LeaveRequest,
        approved_by_user_id: uuid.UUID,
        decision_note: Optional[str] = None,
    ) -> LeaveRequest:
        """Approve a leave request."""
        request.status = LeaveStatusEnum.APPROVED
        request.decided_by_user_id = approved_by_user_id
        request.decided_at = datetime.now(datetime.now().astimezone().tzinfo)
        request.decision_note = decision_note
        db.commit()
        db.refresh(request)
        return request

    @staticmethod
    def reject(
        db: Session,
        request: LeaveRequest,
        rejected_by_user_id: uuid.UUID,
        decision_note: Optional[str] = None,
    ) -> LeaveRequest:
        """Reject a leave request."""
        request.status = LeaveStatusEnum.REJECTED
        request.decided_by_user_id = rejected_by_user_id
        request.decided_at = datetime.now(datetime.now().astimezone().tzinfo)
        request.decision_note = decision_note
        db.commit()
        db.refresh(request)
        return request

    @staticmethod
    def count_pending(db: Session) -> int:
        """Count pending leave requests."""
        return db.query(func.count(LeaveRequest.id)).filter(
            LeaveRequest.status == LeaveStatusEnum.PENDING
        ).scalar() or 0

    @staticmethod
    def count_approved_for_employee(
        db: Session,
        employee_id: uuid.UUID,
    ) -> int:
        """Count approved leave days for an employee."""
        leaves = db.query(LeaveRequest).filter(
            and_(
                LeaveRequest.employee_id == employee_id,
                LeaveRequest.status == LeaveStatusEnum.APPROVED,
            )
        ).all()
        total_days = 0
        for leave in leaves:
            days = (leave.end_date - leave.start_date).days + 1
            total_days += days
        return total_days

    @staticmethod
    def count_pending_for_employee(
        db: Session,
        employee_id: uuid.UUID,
    ) -> int:
        """Count pending leave days for an employee."""
        leaves = db.query(LeaveRequest).filter(
            and_(
                LeaveRequest.employee_id == employee_id,
                LeaveRequest.status == LeaveStatusEnum.PENDING,
            )
        ).all()
        total_days = 0
        for leave in leaves:
            days = (leave.end_date - leave.start_date).days + 1
            total_days += days
        return total_days

    @staticmethod
    def count_rejected_for_employee(
        db: Session,
        employee_id: uuid.UUID,
    ) -> int:
        """Count rejected leave days for an employee."""
        leaves = db.query(LeaveRequest).filter(
            and_(
                LeaveRequest.employee_id == employee_id,
                LeaveRequest.status == LeaveStatusEnum.REJECTED,
            )
        ).all()
        total_days = 0
        for leave in leaves:
            days = (leave.end_date - leave.start_date).days + 1
            total_days += days
        return total_days
