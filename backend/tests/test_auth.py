"""Test cases for authentication."""

import pytest
from fastapi.testclient import TestClient


def test_login_success(client: TestClient, db, employee_user):
    """Test successful login."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": employee_user.email, "password": "emp123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"]
    assert data["user"]["id"] == str(employee_user.id)
    assert data["user"]["email"] == employee_user.email


def test_login_invalid_password(client: TestClient, db, employee_user):
    """Test login with invalid password."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": employee_user.email, "password": "wrongpass"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_inactive_user(client: TestClient, db, inactive_user):
    """Test login with inactive user."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": inactive_user.email, "password": "inactive123"},
    )
    assert response.status_code == 401


def test_login_nonexistent_user(client: TestClient):
    """Test login with nonexistent user."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@test.local", "password": "password"},
    )
    assert response.status_code == 401


def test_get_me(client: TestClient, employee_token: str, employee_user):
    """Test get current user endpoint."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == employee_user.email
    assert data["role"] == "EMPLOYEE"


def test_get_me_unauthorized(client: TestClient):
    """Test get current user without token."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 403
