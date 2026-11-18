"""Tests for liveness and readiness probes."""

from fastapi.testclient import TestClient

from attendflow.database import get_db
from attendflow.main import app


class _UnreachableSession:
    def execute(self, *args, **kwargs):
        raise RuntimeError("connection refused")


def _broken_db():
    yield _UnreachableSession()


def test_live_returns_ok(client):
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_returns_ok_when_database_reachable(client):
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_ready_returns_503_when_database_unreachable():
    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _broken_db
    try:
        response = TestClient(app).get("/health/ready")
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous

    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "unavailable"}
    assert "connection refused" not in response.text
