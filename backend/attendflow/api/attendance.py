"""Attendance tracking API routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import date
import uuid

from attendflow.database import get_db
from attendflow.schemas import (
    AttendanceCheckIn, AttendanceCheckOut, AttendanceResponse, AttendanceListResponse,
    AttendanceTodayResponse
)
from attendflow.services import AttendanceService
from attendflow.security import get_current_user, get_current_admin
from attendflow.models import User
from attendflow.repositories import EmployeeRepository

router = APIRouter(prefix="/api/v1/attendance", tags=["attendance"])


@router.post("/check-in", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
async def check_in(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Check in for today (employee)."""
    # Get employee record
    employee = EmployeeRepository.get_by_user_id(db, user.id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee profile not found",
        )
    
    try:
        return AttendanceService.check_in(db, employee.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.post("/check-out", response_model=AttendanceResponse)
async def check_out(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Check out for today (employee)."""
    # Get employee record
    employee = EmployeeRepository.get_by_user_id(db, user.id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee profile not found",
        )
    
    try:
        return AttendanceService.check_out(db, employee.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get("/me", response_model=AttendanceListResponse)
async def get_my_attendance(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get my attendance history (employee)."""
    # Get employee record
    employee = EmployeeRepository.get_by_user_id(db, user.id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee profile not found",
        )
    
    result = AttendanceService.get_employee_attendance_history(db, employee.id, skip, limit)
    return AttendanceListResponse(**result)


@router.get("", response_model=AttendanceListResponse)
async def list_attendance(
    employee_id: uuid.UUID = Query(None),
    start_date: date = Query(None),
    end_date: date = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """List all attendance records (admin only)."""
    result = AttendanceService.list_attendance(
        db, employee_id, start_date, end_date, skip, limit
    )
    return AttendanceListResponse(**result)


@router.get("/today", response_model=AttendanceTodayResponse)
async def get_today_attendance(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Get today's attendance summary (admin only)."""
    summary = AttendanceService.get_today_summary(db)
    return AttendanceTodayResponse(**summary)
