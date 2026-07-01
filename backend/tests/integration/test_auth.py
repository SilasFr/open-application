"""API auth tests: protected routes require a valid bearer token."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_missing_token_returns_401(unauthed_client: TestClient) -> None:
    response = unauthed_client.get("/api/v1/applications")
    assert response.status_code == 401
    assert response.headers.get("WWW-Authenticate") == "Bearer"


def test_invalid_token_returns_401(unauthed_client: TestClient) -> None:
    response = unauthed_client.get(
        "/api/v1/applications",
        headers={"Authorization": "Bearer not-a-real-jwt"},
    )
    assert response.status_code == 401


def test_health_is_public(unauthed_client: TestClient) -> None:
    # Liveness must not require auth.
    assert unauthed_client.get("/health").status_code == 200
