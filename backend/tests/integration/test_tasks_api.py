"""API-level tests for the application tasks/checklist routes."""

from __future__ import annotations

from fastapi.testclient import TestClient

HEADERS = {"X-User-Id": "user-api"}


def _create_application(client: TestClient) -> str:
    response = client.post(
        "/api/v1/applications",
        json={"company": "Acme", "role": "Engineer"},
        headers=HEADERS,
    )
    return response.json()["id"]


def test_create_and_list_tasks(client: TestClient) -> None:
    application_id = _create_application(client)

    create = client.post(
        f"/api/v1/applications/{application_id}/tasks",
        json={"title": "Send thank-you letter"},
        headers=HEADERS,
    )
    assert create.status_code == 201
    assert create.json()["is_completed"] is False

    listed = client.get(
        f"/api/v1/applications/{application_id}/tasks", headers=HEADERS
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_toggle_task_completion(client: TestClient) -> None:
    application_id = _create_application(client)
    task_id = client.post(
        f"/api/v1/applications/{application_id}/tasks",
        json={"title": "Tailor CV"},
        headers=HEADERS,
    ).json()["id"]

    updated = client.patch(
        f"/api/v1/applications/{application_id}/tasks/{task_id}",
        json={"is_completed": True},
        headers=HEADERS,
    )
    assert updated.status_code == 200
    assert updated.json()["is_completed"] is True


def test_create_task_rejects_empty_title(client: TestClient) -> None:
    application_id = _create_application(client)

    response = client.post(
        f"/api/v1/applications/{application_id}/tasks",
        json={"title": ""},
        headers=HEADERS,
    )
    assert response.status_code == 422


def test_delete_task(client: TestClient) -> None:
    application_id = _create_application(client)
    task_id = client.post(
        f"/api/v1/applications/{application_id}/tasks",
        json={"title": "x"},
        headers=HEADERS,
    ).json()["id"]

    deleted = client.delete(
        f"/api/v1/applications/{application_id}/tasks/{task_id}", headers=HEADERS
    )
    assert deleted.status_code == 204

    listed = client.get(
        f"/api/v1/applications/{application_id}/tasks", headers=HEADERS
    )
    assert listed.json() == []


def test_tasks_for_unowned_application_return_404(client: TestClient) -> None:
    response = client.get(
        "/api/v1/applications/does-not-exist/tasks", headers=HEADERS
    )
    assert response.status_code == 404


def test_tasks_require_authentication(unauthed_client: TestClient) -> None:
    response = unauthed_client.get("/api/v1/applications/some-id/tasks")
    assert response.status_code == 401
