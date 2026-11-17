"""Test cases for attendance."""

import pytest
from datetime import date, datetime, timezone, timedelta
import pytz
from attendflow.models import AttendanceRecord
from attendflow.config import settings


def test_check_in_success(client, db, employee_token, employee_profile):
    """Test successful check-in."""
    response = client.post(
        "/api/v1/attendance/check-in",
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["employee_id"] == str(employee_profile.id)
    assert data["check_in_at"]
    assert data["check_out_at"] is None
    assert data["status"] == "INCOMPLETE"


def test_check_in_duplicate(client, db, employee_token, employee_profile):
    """Test duplicate check-in on same day."""
    # First check-in
    client.post(
        "/api/v1/attendance/check-in",
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    
    # Second check-in should fail
    response = client.post(
        "/api/v1/attendance/check-in",
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    assert response.status_code == 409
    assert "Already checked in" in response.json()["detail"]


def test_check_out_success(client, db, employee_token, employee_profile):
    """Test successful check-out."""
    # Check in first
    client.post(
        "/api/v1/attendance/check-in",
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    
    # Check out
    response = client.post(
        "/api/v1/attendance/check-out",
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["check_out_at"]
    assert data["status"] == "PRESENT"


def test_check_out_without_check_in(client, db, employee_token, employee_profile):
    """Test check-out without check-in."""
    response = client.post(
        "/api/v1/attendance/check-out",
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    assert response.status_code == 409
    assert "No check-in found" in response.json()["detail"]


def test_check_out_duplicate(client, db, employee_token, employee_profile):
    """Test duplicate check-out."""
    # Check in and out
    client.post(
        "/api/v1/attendance/check-in",
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    client.post(
        "/api/v1/attendance/check-out",
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    
    # Try to check out again
    response = client.post(
        "/api/v1/attendance/check-out",
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    assert response.status_code == 409
    assert "Already checked out" in response.json()["detail"]


def test_get_my_attendance(client, db, employee_token, employee_profile):
    """Test get own attendance history."""
    # Create a record
    client.post(
        "/api/v1/attendance/check-in",
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    
    # Get history
    response = client.get(
        "/api/v1/attendance/me",
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert len(data["items"]) > 0


def test_list_attendance_admin_only(client, admin_token, employee_token):
    """Test list attendance requires admin."""
    response = client.get(
        "/api/v1/attendance",
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    assert response.status_code == 403


def test_list_attendance_admin(client, db, admin_token, employee_profile, employee_user):
    """Test admin can list all attendance."""
    # Create a record
    response = client.post(
        "/api/v1/attendance/check-in",
        headers={"Authorization": f"Bearer {employee_user}"},
    )
    
    # List as admin
    response = client.get(
        "/api/v1/attendance",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


def test_today_attendance_admin_only(client, admin_token, employee_token):
    """Test today's attendance summary requires admin."""
    response = client.get(
        "/api/v1/attendance/today",
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    assert response.status_code == 403


def test_today_attendance_summary(client, db, admin_token):
    """Test get today's attendance summary."""
    response = client.get(
        "/api/v1/attendance/today",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_employees" in data
    assert "present_today" in data
    assert "incomplete_today" in data
