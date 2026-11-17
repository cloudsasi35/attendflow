"""Dashboard and reports API routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import date

from attendflow.database import get_db
from attendflow.schemas import (
    AdminDashboardResponse, EmployeeDashboardResponse,
    AttendanceReportResponse, LeaveReportResponse
)
from attendflow.services import DashboardService, AttendanceService, LeaveService
from attendflow.security import get_current_user, get_current_admin
from attendflow.models import User
from attendflow.repositories import EmployeeRepository

router = APIRouter(prefix="/api/v1", tags=["dashboard", "reports"])


@router.get("/dashboard/admin", response_model=AdminDashboardResponse)
async def get_admin_dashboard(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Get admin dashboard metrics."""
    return DashboardService.get_admin_dashboard(db)


@router.get("/dashboard/employee", response_model=EmployeeDashboardResponse)
async def get_employee_dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get employee dashboard."""
    # Get employee record
    employee = EmployeeRepository.get_by_user_id(db, user.id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee profile not found",
        )
    
    return DashboardService.get_employee_dashboard(db, employee.id)


@router.get("/reports/attendance", response_model=AttendanceReportResponse)
async def get_attendance_report(
    employee_id: str = Query(None),
    start_date: date = Query(None),
    end_date: date = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Get attendance report (admin only)."""
    import uuid
    employee_uuid = None
    if employee_id:
        try:
            employee_uuid = uuid.UUID(employee_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid employee ID",
            )
    
    result = AttendanceService.list_attendance(
        db, employee_uuid, start_date, end_date, skip, limit
    )
    return AttendanceReportResponse(**result)


@router.get("/reports/leave", response_model=LeaveReportResponse)
async def get_leave_report(
    status: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Get leave report (admin only)."""
    result = LeaveService.list_leave_requests(db, status, skip, limit)
    return LeaveReportResponse(**result)


@router.get("/reports/attendance/csv")
async def export_attendance_csv(
    employee_id: str = Query(None),
    start_date: date = Query(None),
    end_date: date = Query(None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Export attendance report as CSV (admin only)."""
    import csv
    import io
    from fastapi.responses import StreamingResponse
    import uuid
    
    employee_uuid = None
    if employee_id:
        try:
            employee_uuid = uuid.UUID(employee_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid employee ID",
            )
    
    # Get all records (no pagination for export)
    result = AttendanceService.list_attendance(
        db, employee_uuid, start_date, end_date, 0, 10000
    )
    
    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Employee ID", "Work Date", "Check In", "Check Out", "Status"])
    
    for record in result["items"]:
        writer.writerow([
            str(record.employee_id),
            record.work_date,
            record.check_in_at,
            record.check_out_at or "",
            record.status,
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=attendance_report.csv"},
    )


@router.get("/reports/leave/csv")
async def export_leave_csv(
    status: str = Query(None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Export leave report as CSV (admin only)."""
    import csv
    import io
    from fastapi.responses import StreamingResponse
    
    # Get all records (no pagination for export)
    result = LeaveService.list_leave_requests(db, status, 0, 10000)
    
    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Employee ID", "Start Date", "End Date", "Type", "Status", "Reason", "Decision"])
    
    for record in result["items"]:
        writer.writerow([
            str(record.employee_id),
            record.start_date,
            record.end_date,
            record.leave_type,
            record.status,
            record.reason,
            record.decision_note or "",
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leave_report.csv"},
    )
