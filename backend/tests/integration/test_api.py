"""API-level tests exercising routers through FastAPI's TestClient."""

from __future__ import annotations

from fastapi.testclient import TestClient

HEADERS = {"X-User-Id": "user-api"}


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_list_application(client: TestClient) -> None:
    create = client.post(
        "/api/v1/applications",
        json={"company": "Acme", "role": "Engineer"},
        headers=HEADERS,
    )
    assert create.status_code == 201
    body = create.json()
    assert body["status"] == "saved"

    listed = client.get("/api/v1/applications", headers=HEADERS)
    assert listed.status_code == 200
    assert [a["id"] for a in listed.json()] == [body["id"]]


def test_status_transition_and_conflict(client: TestClient) -> None:
    created = client.post(
        "/api/v1/applications",
        json={"company": "Acme", "role": "Engineer"},
        headers=HEADERS,
    ).json()
    app_id = created["id"]

    ok = client.patch(
        f"/api/v1/applications/{app_id}/status",
        json={"status": "applied"},
        headers=HEADERS,
    )
    assert ok.status_code == 200
    assert ok.json()["status"] == "applied"

    # saved -> offer is illegal; but we're now at applied, applied -> saved is illegal too.
    conflict = client.patch(
        f"/api/v1/applications/{app_id}/status",
        json={"status": "saved"},
        headers=HEADERS,
    )
    assert conflict.status_code == 409


def test_get_missing_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/applications/nope", headers=HEADERS)
    assert response.status_code == 404


# CV base-resume and tailoring endpoint tests live in test_cv_api.py — the
# tailor flow now requires a saved base resume rather than accepting raw
# cv_text (see specs/004-ui-redesign/contracts/cv-api.md).
