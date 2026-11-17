"""Test cases for leave requests."""

import pytest
from datetime import date, timedelta


def test_create_leave_request(client, db, employee_token, employee_profile):
    """Test creating a leave request."""
    start_date = date.today() + timedelta(days=7)
    end_date = start_date + timedelta(days=2)
    
    response = client.post(
        "/api/v1/leave-requests",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={
            "leave_type": "CASUAL",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "reason": "Test leave",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "PENDING"
    assert data["leave_type"] == "CASUAL"


def test_leave_request_invalid_date_range(client, db, employee_token):
    """Test leave request with invalid date range."""
    end_date = date.today()
    start_date = end_date + timedelta(days=2)
    
    response = client.post(
        "/api/v1/leave-requests",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={
            "leave_type": "CASUAL",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "reason": "Test leave",
        },
    )
    assert response.status_code == 422


def test_overlapping_leave_requests(client, db, employee_token, employee_profile):
    """Test that overlapping leave requests are rejected."""
    start_date = date.today() + timedelta(days=7)
    end_date = start_date + timedelta(days=2)
    
    # Create first request
    response = client.post(
        "/api/v1/leave-requests",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={
            "leave_type": "CASUAL",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "reason": "First leave",
        },
    )
    assert response.status_code == 201
    
    # Try to create overlapping request
    response = client.post(
        "/api/v1/leave-requests",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={
            "leave_type": "CASUAL",
            "start_date": (start_date + timedelta(days=1)).isoformat(),
            "end_date": (end_date + timedelta(days=1)).isoformat(),
            "reason": "Second leave",
        },
    )
    assert response.status_code == 409


def test_get_my_leave_requests(client, db, employee_token):
    """Test get own leave requests."""
    response = client.get(
        "/api/v1/leave-requests/me",
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_list_leave_requests_admin_only(client, employee_token):
    """Test list leave requests requires admin."""
    response = client.get(
        "/api/v1/leave-requests",
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    assert response.status_code == 403


def test_list_leave_requests_admin(client, db, admin_token):
    """Test admin can list leave requests."""
    response = client.get(
        "/api/v1/leave-requests",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


def test_approve_leave_request_admin_only(client, db, admin_token, employee_token, employee_profile):
    """Test approving leave requires admin."""
    # Create a leave request
    start_date = date.today() + timedelta(days=7)
    end_date = start_date + timedelta(days=2)
    
    response = client.post(
        "/api/v1/leave-requests",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={
            "leave_type": "CASUAL",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "reason": "Test leave",
        },
    )
    request_id = response.json()["id"]
    
    # Try to approve as employee
    response = client.post(
        f"/api/v1/leave-requests/{request_id}/approve",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={"decision_note": "Approved"},
    )
    assert response.status_code == 403


def test_approve_leave_request(client, db, admin_token, employee_token, employee_profile):
    """Test admin can approve leave."""
    # Create a leave request
    start_date = date.today() + timedelta(days=7)
    end_date = start_date + timedelta(days=2)
    
    response = client.post(
        "/api/v1/leave-requests",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={
            "leave_type": "CASUAL",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "reason": "Test leave",
        },
    )
    request_id = response.json()["id"]
    
    # Approve as admin
    response = client.post(
        f"/api/v1/leave-requests/{request_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"decision_note": "Approved"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "APPROVED"
    assert data["decision_note"] == "Approved"


def test_reject_leave_request(client, db, admin_token, employee_token, employee_profile):
    """Test admin can reject leave."""
    # Create a leave request
    start_date = date.today() + timedelta(days=7)
    end_date = start_date + timedelta(days=2)
    
    response = client.post(
        "/api/v1/leave-requests",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={
            "leave_type": "CASUAL",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "reason": "Test leave",
        },
    )
    request_id = response.json()["id"]
    
    # Reject as admin
    response = client.post(
        f"/api/v1/leave-requests/{request_id}/reject",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"decision_note": "Not approved"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "REJECTED"
