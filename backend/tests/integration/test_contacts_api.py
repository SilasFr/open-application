"""API-level tests for the application contacts routes."""

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


def test_create_and_list_contacts(client: TestClient) -> None:
    application_id = _create_application(client)

    create = client.post(
        f"/api/v1/applications/{application_id}/contacts",
        json={"name": "Jane Recruiter", "role": "Recruiter", "email": "jane@example.com"},
        headers=HEADERS,
    )
    assert create.status_code == 201
    assert create.json()["email"] == "jane@example.com"

    listed = client.get(
        f"/api/v1/applications/{application_id}/contacts", headers=HEADERS
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_create_contact_rejects_bad_email(client: TestClient) -> None:
    application_id = _create_application(client)

    response = client.post(
        f"/api/v1/applications/{application_id}/contacts",
        json={"name": "Jane", "email": "not-an-email"},
        headers=HEADERS,
    )
    assert response.status_code == 422


def test_create_contact_rejects_bad_url(client: TestClient) -> None:
    application_id = _create_application(client)

    response = client.post(
        f"/api/v1/applications/{application_id}/contacts",
        json={"name": "Jane", "linkedin_url": "not-a-url"},
        headers=HEADERS,
    )
    assert response.status_code == 422


def test_create_contact_rejects_empty_name(client: TestClient) -> None:
    application_id = _create_application(client)

    response = client.post(
        f"/api/v1/applications/{application_id}/contacts",
        json={"name": ""},
        headers=HEADERS,
    )
    assert response.status_code == 422


def test_update_contact(client: TestClient) -> None:
    application_id = _create_application(client)
    contact_id = client.post(
        f"/api/v1/applications/{application_id}/contacts",
        json={"name": "Jane"},
        headers=HEADERS,
    ).json()["id"]

    updated = client.patch(
        f"/api/v1/applications/{application_id}/contacts/{contact_id}",
        json={"linkedin_url": "https://linkedin.com/in/jane"},
        headers=HEADERS,
    )
    assert updated.status_code == 200
    assert updated.json()["linkedin_url"] == "https://linkedin.com/in/jane"


def test_delete_contact(client: TestClient) -> None:
    application_id = _create_application(client)
    contact_id = client.post(
        f"/api/v1/applications/{application_id}/contacts",
        json={"name": "Jane"},
        headers=HEADERS,
    ).json()["id"]

    deleted = client.delete(
        f"/api/v1/applications/{application_id}/contacts/{contact_id}", headers=HEADERS
    )
    assert deleted.status_code == 204

    listed = client.get(
        f"/api/v1/applications/{application_id}/contacts", headers=HEADERS
    )
    assert listed.json() == []


def test_contacts_for_unowned_application_return_404(client: TestClient) -> None:
    response = client.get(
        "/api/v1/applications/does-not-exist/contacts", headers=HEADERS
    )
    assert response.status_code == 404


def test_contacts_require_authentication(unauthed_client: TestClient) -> None:
    response = unauthed_client.get("/api/v1/applications/some-id/contacts")
    assert response.status_code == 401
