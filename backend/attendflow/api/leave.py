"""Leave request API routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import uuid

from attendflow.database import get_db
from attendflow.schemas import (
    LeaveRequestCreate, LeaveRequestApprove, LeaveRequestReject,
    LeaveRequestResponse, LeaveRequestListResponse
)
from attendflow.services import LeaveService
from attendflow.security import get_current_user, get_current_admin
from attendflow.models import User, LeaveStatusEnum
from attendflow.repositories import EmployeeRepository

router = APIRouter(prefix="/api/v1/leave-requests", tags=["leave"])


@router.post("", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_leave_request(
    data: LeaveRequestCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a leave request (employee)."""
    # Get employee record
    employee = EmployeeRepository.get_by_user_id(db, user.id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee profile not found",
        )
    
    try:
        return LeaveService.request_leave(db, employee.id, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get("/me", response_model=LeaveRequestListResponse)
async def get_my_leave_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get my leave requests (employee)."""
    # Get employee record
    employee = EmployeeRepository.get_by_user_id(db, user.id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee profile not found",
        )
    
    result = LeaveService.get_employee_leave_requests(db, employee.id, skip, limit)
    return LeaveRequestListResponse(**result)


@router.get("", response_model=LeaveRequestListResponse)
async def list_leave_requests(
    status: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """List all leave requests (admin only)."""
    result = LeaveService.list_leave_requests(db, status, skip, limit)
    return LeaveRequestListResponse(**result)


@router.post("/{request_id}/approve", response_model=LeaveRequestResponse)
async def approve_leave_request(
    request_id: uuid.UUID,
    data: LeaveRequestApprove,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Approve a leave request (admin only)."""
    try:
        return LeaveService.approve_leave(db, request_id, admin.id, data.decision_note)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in str(e) else status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.post("/{request_id}/reject", response_model=LeaveRequestResponse)
async def reject_leave_request(
    request_id: uuid.UUID,
    data: LeaveRequestReject,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Reject a leave request (admin only)."""
    try:
        return LeaveService.reject_leave(db, request_id, admin.id, data.decision_note)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in str(e) else status.HTTP_409_CONFLICT,
            detail=str(e),
        )
