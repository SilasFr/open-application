"""API-level tests for the application timeline/notes routes."""

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


def test_create_and_list_notes(client: TestClient) -> None:
    application_id = _create_application(client)

    create = client.post(
        f"/api/v1/applications/{application_id}/notes",
        json={"content": "Recruiter called"},
        headers=HEADERS,
    )
    assert create.status_code == 201
    assert create.json()["type"] == "note"

    listed = client.get(
        f"/api/v1/applications/{application_id}/notes", headers=HEADERS
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_status_change_appears_as_activity_in_timeline(client: TestClient) -> None:
    application_id = _create_application(client)

    client.patch(
        f"/api/v1/applications/{application_id}/status",
        json={"status": "applied"},
        headers=HEADERS,
    )

    listed = client.get(
        f"/api/v1/applications/{application_id}/notes", headers=HEADERS
    )
    assert listed.status_code == 200
    body = listed.json()
    assert len(body) == 1
    assert body[0]["type"] == "activity"
    assert body[0]["content"] == "Moved to Applied"


def test_update_note_sets_edited_timestamp(client: TestClient) -> None:
    application_id = _create_application(client)
    note_id = client.post(
        f"/api/v1/applications/{application_id}/notes",
        json={"content": "Original"},
        headers=HEADERS,
    ).json()["id"]

    updated = client.patch(
        f"/api/v1/applications/{application_id}/notes/{note_id}",
        json={"content": "Edited"},
        headers=HEADERS,
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["content"] == "Edited"
    assert body["updated_at"] >= body["created_at"]


def test_delete_note(client: TestClient) -> None:
    application_id = _create_application(client)
    note_id = client.post(
        f"/api/v1/applications/{application_id}/notes",
        json={"content": "x"},
        headers=HEADERS,
    ).json()["id"]

    deleted = client.delete(
        f"/api/v1/applications/{application_id}/notes/{note_id}", headers=HEADERS
    )
    assert deleted.status_code == 204

    listed = client.get(
        f"/api/v1/applications/{application_id}/notes", headers=HEADERS
    )
    assert listed.json() == []


def test_notes_for_unowned_application_return_404(client: TestClient) -> None:
    response = client.get(
        "/api/v1/applications/does-not-exist/notes", headers=HEADERS
    )
    assert response.status_code == 404


def test_create_note_empty_content_rejected(client: TestClient) -> None:
    application_id = _create_application(client)

    response = client.post(
        f"/api/v1/applications/{application_id}/notes",
        json={"content": ""},
        headers=HEADERS,
    )
    assert response.status_code == 422


def test_notes_require_authentication(unauthed_client: TestClient) -> None:
    response = unauthed_client.get("/api/v1/applications/some-id/notes")
    assert response.status_code == 401
