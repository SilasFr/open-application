"""API-level tests for the base-resume and CV-tailoring routes."""

from __future__ import annotations

import io

from docx import Document
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

HEADERS = {"X-User-Id": "user-api"}

DOCX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)
PDF_CONTENT_TYPE = "application/pdf"


def _build_docx_bytes(text: str) -> bytes:
    document = Document()
    for line in text.splitlines():
        document.add_paragraph(line)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def _build_pdf_bytes(text: str) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(72, 750, text)
    pdf.save()
    return buffer.getvalue()


def _upload_base_resume(
    client: TestClient, *, text: str = "Jane Doe\nPython engineer with 5 years experience."
) -> dict[str, object]:
    files = {
        "file": ("resume.docx", _build_docx_bytes(text), DOCX_CONTENT_TYPE),
    }
    response = client.post("/api/v1/cv/base", files=files, headers=HEADERS)
    assert response.status_code == 201, response.text
    return dict(response.json())


# --- Base resume ------------------------------------------------------------


def test_get_base_resume_returns_404_when_none_saved(client: TestClient) -> None:
    response = client.get("/api/v1/cv/base", headers=HEADERS)
    assert response.status_code == 404


def test_upload_and_fetch_base_resume(client: TestClient) -> None:
    uploaded = _upload_base_resume(client)
    assert uploaded["filename"] == "resume.docx"
    assert "id" in uploaded
    assert "created_at" in uploaded

    fetched = client.get("/api/v1/cv/base", headers=HEADERS)
    assert fetched.status_code == 200
    assert fetched.json()["id"] == uploaded["id"]


def test_upload_pdf_base_resume(client: TestClient) -> None:
    files = {
        "file": ("resume.pdf", _build_pdf_bytes("Jane Doe"), PDF_CONTENT_TYPE),
    }
    response = client.post("/api/v1/cv/base", files=files, headers=HEADERS)
    assert response.status_code == 201, response.text
    assert response.json()["filename"] == "resume.pdf"


def test_upload_rejects_unsupported_file_type(client: TestClient) -> None:
    files = {"file": ("resume.txt", b"plain text resume", "text/plain")}
    response = client.post("/api/v1/cv/base", files=files, headers=HEADERS)
    assert response.status_code == 400


def test_upload_rejects_oversized_file(client: TestClient) -> None:
    oversized = b"%PDF-1.4\n" + b"0" * (5 * 1024 * 1024 + 1)
    files = {"file": ("resume.pdf", oversized, PDF_CONTENT_TYPE)}
    response = client.post("/api/v1/cv/base", files=files, headers=HEADERS)
    assert response.status_code == 400


def test_replace_base_resume_keeps_only_one(client: TestClient) -> None:
    first = _upload_base_resume(client, text="First resume")
    second = _upload_base_resume(client, text="Second resume")
    assert first["id"] != second["id"]

    fetched = client.get("/api/v1/cv/base", headers=HEADERS)
    assert fetched.json()["id"] == second["id"]


def test_delete_base_resume(client: TestClient) -> None:
    _upload_base_resume(client)
    deleted = client.delete("/api/v1/cv/base", headers=HEADERS)
    assert deleted.status_code == 204

    fetched = client.get("/api/v1/cv/base", headers=HEADERS)
    assert fetched.status_code == 404


def test_base_resume_requires_authentication(unauthed_client: TestClient) -> None:
    response = unauthed_client.get("/api/v1/cv/base")
    assert response.status_code == 401


# --- Tailoring ---------------------------------------------------------------


def test_tailor_requires_base_resume(client: TestClient) -> None:
    response = client.post(
        "/api/v1/cv/tailor",
        json={"job_description": "Looking for a Python engineer"},
        headers=HEADERS,
    )
    assert response.status_code == 404
    # The frontend routes the user back to the upload step off this stable code,
    # not the human-readable message — keep them in sync.
    assert response.json()["code"] == "base_resume_not_found"


def test_get_base_resume_404_carries_base_resume_not_found_code(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/cv/base", headers=HEADERS)
    assert response.status_code == 404
    assert response.json()["code"] == "base_resume_not_found"


def test_tailor_cv_returns_structured_sections(client: TestClient) -> None:
    _upload_base_resume(client)

    response = client.post(
        "/api/v1/cv/tailor",
        json={"job_description": "Looking for a Python engineer"},
        headers=HEADERS,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["sections"][0]["id"] == "summary"
    assert body["sections"][0]["bullets"]
    assert body["application_id"] is None
    return_id = body["id"]

    fetched = client.get(f"/api/v1/cv/tailored/{return_id}", headers=HEADERS)
    assert fetched.status_code == 200
    assert fetched.json()["id"] == return_id


def test_tailor_cv_rejects_empty_job_description(client: TestClient) -> None:
    _upload_base_resume(client)
    response = client.post(
        "/api/v1/cv/tailor",
        json={"job_description": ""},
        headers=HEADERS,
    )
    # Pydantic min_length=1 rejects before the service — 422.
    assert response.status_code == 422


def test_tailored_cv_not_found_for_other_user(client: TestClient) -> None:
    response = client.get("/api/v1/cv/tailored/does-not-exist", headers=HEADERS)
    assert response.status_code == 404


def test_tailor_cv_requires_authentication(unauthed_client: TestClient) -> None:
    response = unauthed_client.post(
        "/api/v1/cv/tailor", json={"job_description": "role"}
    )
    assert response.status_code == 401


# --- Refinement ---------------------------------------------------------------


def test_refine_tailored_cv(client: TestClient) -> None:
    _upload_base_resume(client)
    first = client.post(
        "/api/v1/cv/tailor",
        json={"job_description": "Looking for a Python engineer"},
        headers=HEADERS,
    ).json()

    refined = client.post(
        "/api/v1/cv/tailor",
        json={
            "job_description": "Looking for a Python engineer",
            "refinement_instructions": "Keep it to one page.",
            "previous_tailored_cv_id": first["id"],
        },
        headers=HEADERS,
    )
    assert refined.status_code == 201, refined.text
    body = refined.json()
    assert body["previous_tailored_cv_id"] == first["id"]
    assert body["id"] != first["id"]


def test_refine_rejects_empty_instructions(client: TestClient) -> None:
    _upload_base_resume(client)
    first = client.post(
        "/api/v1/cv/tailor",
        json={"job_description": "role"},
        headers=HEADERS,
    ).json()

    response = client.post(
        "/api/v1/cv/tailor",
        json={
            "job_description": "role",
            "refinement_instructions": "",
            "previous_tailored_cv_id": first["id"],
        },
        headers=HEADERS,
    )
    # Pydantic min_length=1 rejects before the service — 422.
    assert response.status_code == 422


def test_refine_unknown_previous_tailored_cv_returns_404(client: TestClient) -> None:
    _upload_base_resume(client)
    response = client.post(
        "/api/v1/cv/tailor",
        json={
            "job_description": "role",
            "refinement_instructions": "Trim it down.",
            "previous_tailored_cv_id": "does-not-exist",
        },
        headers=HEADERS,
    )
    assert response.status_code == 404


# --- Attach to application -----------------------------------------------------


def test_attach_tailored_cv_to_application(client: TestClient) -> None:
    _upload_base_resume(client)
    tailored = client.post(
        "/api/v1/cv/tailor",
        json={"job_description": "role"},
        headers=HEADERS,
    ).json()
    application = client.post(
        "/api/v1/applications",
        json={"company": "Acme", "role": "Engineer"},
        headers=HEADERS,
    ).json()

    attached = client.post(
        f"/api/v1/cv/tailored/{tailored['id']}/attach",
        json={"application_id": application["id"]},
        headers=HEADERS,
    )
    assert attached.status_code == 200, attached.text
    assert attached.json()["application_id"] == application["id"]


def test_attach_to_unowned_application_returns_404(client: TestClient) -> None:
    _upload_base_resume(client)
    tailored = client.post(
        "/api/v1/cv/tailor",
        json={"job_description": "role"},
        headers=HEADERS,
    ).json()

    response = client.post(
        f"/api/v1/cv/tailored/{tailored['id']}/attach",
        json={"application_id": "does-not-exist"},
        headers=HEADERS,
    )
    assert response.status_code == 404


def test_attach_unowned_tailored_cv_returns_404(client: TestClient) -> None:
    application = client.post(
        "/api/v1/applications",
        json={"company": "Acme", "role": "Engineer"},
        headers=HEADERS,
    ).json()

    response = client.post(
        "/api/v1/cv/tailored/does-not-exist/attach",
        json={"application_id": application["id"]},
        headers=HEADERS,
    )
    assert response.status_code == 404


# --- Download -------------------------------------------------------------------


def test_download_tailored_cv_pdf(client: TestClient) -> None:
    _upload_base_resume(client)
    tailored = client.post(
        "/api/v1/cv/tailor",
        json={"job_description": "role"},
        headers=HEADERS,
    ).json()

    response = client.get(
        f"/api/v1/cv/tailored/{tailored['id']}/download",
        params={"format": "pdf"},
        headers=HEADERS,
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == PDF_CONTENT_TYPE
    assert "attachment" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF")


def test_download_tailored_cv_docx(client: TestClient) -> None:
    _upload_base_resume(client)
    tailored = client.post(
        "/api/v1/cv/tailor",
        json={"job_description": "role"},
        headers=HEADERS,
    ).json()

    response = client.get(
        f"/api/v1/cv/tailored/{tailored['id']}/download",
        params={"format": "docx"},
        headers=HEADERS,
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == DOCX_CONTENT_TYPE


def test_download_rejects_invalid_format(client: TestClient) -> None:
    _upload_base_resume(client)
    tailored = client.post(
        "/api/v1/cv/tailor",
        json={"job_description": "role"},
        headers=HEADERS,
    ).json()

    response = client.get(
        f"/api/v1/cv/tailored/{tailored['id']}/download",
        params={"format": "txt"},
        headers=HEADERS,
    )
    assert response.status_code == 400


def test_download_unowned_tailored_cv_returns_404(client: TestClient) -> None:
    response = client.get(
        "/api/v1/cv/tailored/does-not-exist/download",
        params={"format": "pdf"},
        headers=HEADERS,
    )
    assert response.status_code == 404


def test_malformed_ai_response_returns_422() -> None:
    """A malformed/non-JSON AI response surfaces as 422 through the real HTTP
    stack (not just at the unit level). Builds its own app instance with a
    FakeAIClient wired to return invalid output, since the shared `client`
    fixture's AI double always returns valid structured JSON."""
    from app.core.dependencies import get_cv_service, get_cv_tailoring_service
    from app.core.security import get_current_user_id
    from app.main import create_app
    from app.services.cv_service import CVService
    from app.services.cv_tailoring_service import CVTailoringService
    from tests.fakes import (
        FakeAIClient,
        FakeAIClientResolver,
        InMemoryApplicationRepository,
        InMemoryCVRepository,
        InMemoryTailoredCVRepository,
    )
    from tests.integration.conftest import TEST_PROMPTS

    app = create_app()
    cv_repository = InMemoryCVRepository()
    tailored_repository = InMemoryTailoredCVRepository()
    application_repository = InMemoryApplicationRepository()
    app.dependency_overrides[get_current_user_id] = lambda: "user-api"
    app.dependency_overrides[get_cv_service] = lambda: CVService(cv_repository)
    app.dependency_overrides[get_cv_tailoring_service] = lambda: CVTailoringService(
        FakeAIClientResolver(FakeAIClient(response="not valid json at all")),
        TEST_PROMPTS,
        cv_repository,
        tailored_repository,
        application_repository,
    )

    with TestClient(app) as broken_client:
        _upload_base_resume(broken_client)
        response = broken_client.post(
            "/api/v1/cv/tailor",
            json={"job_description": "role"},
            headers=HEADERS,
        )
    assert response.status_code == 422
