"""Unit tests for CVTailoringService against fakes (no network)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.domain.ai import AIClient
from app.domain.entities import (
    CV,
    Application,
    ContactLink,
    TailoredCV,
    TailoredCVContact,
    TailoredCVEntry,
    TailoredCVSection,
)
from app.domain.exceptions import (
    AIGenerationError,
    DomainError,
    InvalidAIResponseError,
    NotFoundError,
)
from app.domain.value_objects import ApplicationStatus
from app.services.cv_tailoring_service import CVTailoringService
from tests.fakes import (
    DEFAULT_STRUCTURED_AI_RESPONSE,
    FakeAIClient,
    InMemoryApplicationRepository,
    InMemoryCVRepository,
    InMemoryTailoredCVRepository,
)

TEMPLATE = (
    "CV:\n{{CV}}\n\nJD:\n{{JOB_DESCRIPTION}}\n\n"
    "PREVIOUS:\n{{PREVIOUS_TAILORED_CV}}\n\nREFINE:\n{{REFINEMENT_INSTRUCTIONS}}"
)


def _make_service(
    ai_client: FakeAIClient | None = None,
) -> tuple[
    CVTailoringService,
    InMemoryCVRepository,
    InMemoryTailoredCVRepository,
    InMemoryApplicationRepository,
]:
    cv_repository = InMemoryCVRepository()
    tailored_repository = InMemoryTailoredCVRepository()
    application_repository = InMemoryApplicationRepository()
    service = CVTailoringService(
        ai_client or FakeAIClient(),
        TEMPLATE,
        cv_repository,
        tailored_repository,
        application_repository,
    )
    return service, cv_repository, tailored_repository, application_repository


async def _seed_base_resume(repository: InMemoryCVRepository, user_id: str) -> CV:
    cv = CV(
        id=str(uuid4()),
        user_id=user_id,
        filename="resume.docx",
        storage_path=f"{user_id}/resume.docx",
        created_at=datetime.now(UTC),
        content="Jane Doe, Python engineer",
    )
    return await repository.replace(cv, b"docx-bytes", "application/docx")


async def test_tailor_fills_template_and_returns_structured_sections() -> None:
    ai = FakeAIClient(response=DEFAULT_STRUCTURED_AI_RESPONSE)
    service, cv_repository, _, _ = _make_service(ai)
    await _seed_base_resume(cv_repository, "user-1")

    result = await service.tailor(
        user_id="user-1", job_description="Seeking a Python engineer"
    )

    assert result.user_id == "user-1"
    assert result.contact is not None
    assert result.contact.name == "Jane Doe"
    assert len(result.sections) == 2
    summary = result.sections[0]
    assert summary.changed is True
    assert summary.explanation
    assert summary.body
    # The structured experience section carries entries, not prose body.
    experience = result.sections[1]
    assert experience.body is None
    assert experience.entries[0].title == "Software Engineer"
    assert experience.entries[0].bullets
    assert "Summary" in result.content
    # Entry content is flattened into the stored plain-text content too.
    assert "Software Engineer" in result.content
    # The template placeholders were substituted before hitting the client.
    assert ai.last_prompt is not None
    assert "Jane Doe, Python engineer" in ai.last_prompt
    assert "Seeking a Python engineer" in ai.last_prompt
    assert "{{CV}}" not in ai.last_prompt


async def test_tailor_without_base_resume_raises_not_found() -> None:
    service, _, _, _ = _make_service()

    with pytest.raises(NotFoundError):
        await service.tailor(user_id="user-1", job_description="JD")


async def test_empty_job_description_raises() -> None:
    service, cv_repository, _, _ = _make_service()
    await _seed_base_resume(cv_repository, "user-1")

    with pytest.raises(DomainError):
        await service.tailor(user_id="user-1", job_description="   ")


async def test_ai_client_failure_raises_ai_generation_error() -> None:
    """A vendor SDK failure (auth, rate limit, network, outage — modeled here as
    a generic RuntimeError since the service must not depend on any specific
    provider's exception types) surfaces as a clean, retryable AIGenerationError
    instead of an unhandled exception."""
    ai = FakeAIClient(error=RuntimeError("429 RESOURCE_EXHAUSTED"))
    service, cv_repository, _, _ = _make_service(ai)
    await _seed_base_resume(cv_repository, "user-1")

    with pytest.raises(AIGenerationError):
        await service.tailor(user_id="user-1", job_description="JD")


async def test_malformed_json_raises_invalid_ai_response() -> None:
    ai = FakeAIClient(response="not json at all")
    service, cv_repository, _, _ = _make_service(ai)
    await _seed_base_resume(cv_repository, "user-1")

    with pytest.raises(InvalidAIResponseError):
        await service.tailor(user_id="user-1", job_description="JD")


class _SequenceAIClient(AIClient):
    """Returns queued responses in order, counting calls — models a provider
    whose first structured output is malformed and whose next one is valid."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = responses
        self.calls = 0

    async def generate(self, *, system: str, prompt: str) -> str:
        response = self._responses[self.calls]
        self.calls += 1
        return response


async def test_retries_once_on_malformed_output_then_succeeds() -> None:
    # First response is invalid JSON (transient small-model glitch), second is
    # valid — tailor() should recover rather than surface an error.
    ai = _SequenceAIClient(["null on a field, not json", DEFAULT_STRUCTURED_AI_RESPONSE])
    service, cv_repository, _, _ = _make_service()
    service._ai_client = ai  # type: ignore[assignment]
    await _seed_base_resume(cv_repository, "user-1")

    result = await service.tailor(user_id="user-1", job_description="JD")

    assert result.sections  # a valid tailored CV came back
    assert ai.calls == 2  # exactly one retry


async def test_gives_up_after_max_attempts_on_persistent_malformed_output() -> None:
    ai = _SequenceAIClient(["bad one", "bad two", "bad three", "bad four"])
    service, cv_repository, _, _ = _make_service()
    service._ai_client = ai  # type: ignore[assignment]
    await _seed_base_resume(cv_repository, "user-1")

    with pytest.raises(InvalidAIResponseError):
        await service.tailor(user_id="user-1", job_description="JD")
    assert ai.calls == 3  # bounded to _MAX_GENERATION_ATTEMPTS — no infinite retry


async def test_missing_sections_key_raises_invalid_ai_response() -> None:
    ai = FakeAIClient(response=json.dumps({"not_sections": []}))
    service, cv_repository, _, _ = _make_service(ai)
    await _seed_base_resume(cv_repository, "user-1")

    with pytest.raises(InvalidAIResponseError):
        await service.tailor(user_id="user-1", job_description="JD")


async def test_empty_sections_list_raises_invalid_ai_response() -> None:
    ai = FakeAIClient(response=json.dumps({"sections": []}))
    service, cv_repository, _, _ = _make_service(ai)
    await _seed_base_resume(cv_repository, "user-1")

    with pytest.raises(InvalidAIResponseError):
        await service.tailor(user_id="user-1", job_description="JD")


async def test_changed_section_without_explanation_raises_invalid_ai_response() -> None:
    ai = FakeAIClient(
        response=json.dumps(
            {
                "contact": {"name": "Jane Doe"},
                "sections": [
                    {
                        "id": "summary",
                        "heading": "Summary",
                        "body": "...",
                        "changed": True,
                        "explanation": None,
                    }
                ],
            }
        )
    )
    service, cv_repository, _, _ = _make_service(ai)
    await _seed_base_resume(cv_repository, "user-1")

    with pytest.raises(InvalidAIResponseError):
        await service.tailor(user_id="user-1", job_description="JD")


async def test_empty_refinement_instructions_raises() -> None:
    service, cv_repository, _, _ = _make_service()
    await _seed_base_resume(cv_repository, "user-1")

    with pytest.raises(DomainError):
        await service.tailor(
            user_id="user-1", job_description="JD", refinement_instructions="   "
        )


async def test_refinement_includes_previous_content_and_instructions_in_prompt() -> None:
    ai = FakeAIClient(response=DEFAULT_STRUCTURED_AI_RESPONSE)
    service, cv_repository, _, _ = _make_service(ai)
    await _seed_base_resume(cv_repository, "user-1")

    first = await service.tailor(user_id="user-1", job_description="JD")

    refined = await service.tailor(
        user_id="user-1",
        job_description="JD",
        refinement_instructions="Keep it to one page.",
        previous_tailored_cv_id=first.id,
    )

    assert refined.previous_tailored_cv_id == first.id
    assert refined.refinement_instructions == "Keep it to one page."
    assert ai.last_prompt is not None
    assert "Keep it to one page." in ai.last_prompt
    assert first.content in ai.last_prompt


async def test_refinement_with_unknown_previous_id_raises_not_found() -> None:
    service, cv_repository, _, _ = _make_service()
    await _seed_base_resume(cv_repository, "user-1")

    with pytest.raises(NotFoundError):
        await service.tailor(
            user_id="user-1",
            job_description="JD",
            refinement_instructions="Trim it.",
            previous_tailored_cv_id="does-not-exist",
        )


async def test_get_owned_raises_not_found_for_other_user() -> None:
    service, cv_repository, _, _ = _make_service()
    await _seed_base_resume(cv_repository, "user-1")
    tailored = await service.tailor(user_id="user-1", job_description="JD")

    with pytest.raises(NotFoundError):
        await service.get_owned("someone-else", tailored.id)


async def test_attach_sets_application_id() -> None:
    service, cv_repository, _, application_repository = _make_service()
    await _seed_base_resume(cv_repository, "user-1")
    tailored = await service.tailor(user_id="user-1", job_description="JD")

    application = Application(
        id=str(uuid4()),
        user_id="user-1",
        company="Acme",
        role="Engineer",
        status=ApplicationStatus.SAVED,
        job_description=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    await application_repository.add(application)

    updated = await service.attach("user-1", tailored.id, application.id)

    assert updated.application_id == application.id


async def test_attach_to_unowned_application_raises_not_found() -> None:
    service, cv_repository, _, _ = _make_service()
    await _seed_base_resume(cv_repository, "user-1")
    tailored = await service.tailor(user_id="user-1", job_description="JD")

    with pytest.raises(NotFoundError):
        await service.attach("user-1", tailored.id, "does-not-exist")


async def test_section_without_body_or_entries_raises_invalid_ai_response() -> None:
    ai = FakeAIClient(
        response=json.dumps(
            {
                "contact": {"name": "Jane Doe"},
                "sections": [
                    {
                        "id": "summary",
                        "heading": "Summary",
                        "body": None,
                        "entries": [],
                        "changed": False,
                        "explanation": None,
                    }
                ],
            }
        )
    )
    service, cv_repository, _, _ = _make_service(ai)
    await _seed_base_resume(cv_repository, "user-1")

    with pytest.raises(InvalidAIResponseError):
        await service.tailor(user_id="user-1", job_description="JD")


async def test_render_with_contact_and_entries_produces_bytes() -> None:
    service, _, _, _ = _make_service()
    tailored = TailoredCV(
        id=str(uuid4()),
        user_id="user-1",
        source_cv_id=None,
        job_description="JD",
        content="...",
        created_at=datetime.now(UTC),
        contact=TailoredCVContact(
            name="Jane Doe",
            email="jane@example.com",
            location="Remote",
            links=[ContactLink(label="GitHub", url="https://github.com/janedoe")],
        ),
        sections=[
            TailoredCVSection(
                id="experience",
                heading="Professional Experience",
                changed=True,
                entries=[
                    TailoredCVEntry(
                        title="Senior Engineer",
                        organization="Foo Inc",
                        date_range="2020 – 2024",
                        context="Fintech",
                        bullets=["Built <Python> & Go APIs.", "Owned reliability."],
                    )
                ],
                explanation="Led with the most relevant role.",
            )
        ],
    )

    pdf_bytes, _, _ = await service.render(tailored, format="pdf")
    docx_bytes, _, _ = await service.render(tailored, format="docx")
    assert pdf_bytes.startswith(b"%PDF")
    assert docx_bytes.startswith(b"PK")


async def test_render_pdf_and_docx_produce_bytes() -> None:
    service, _, _, _ = _make_service()
    tailored = TailoredCV(
        id=str(uuid4()),
        user_id="user-1",
        source_cv_id=None,
        job_description="JD",
        content="Summary\nExperienced engineer.",
        created_at=datetime.now(UTC),
        sections=[
            TailoredCVSection(
                id="summary",
                heading="Summary",
                body="Experienced engineer.",
                changed=False,
                explanation=None,
            )
        ],
    )

    pdf_bytes, pdf_content_type, pdf_filename = await service.render(
        tailored, format="pdf"
    )
    assert pdf_bytes.startswith(b"%PDF")
    assert pdf_content_type == "application/pdf"
    assert pdf_filename.endswith(".pdf")

    docx_bytes, docx_content_type, docx_filename = await service.render(
        tailored, format="docx"
    )
    assert docx_bytes.startswith(b"PK")  # DOCX is a zip archive
    assert "wordprocessingml" in docx_content_type
    assert docx_filename.endswith(".docx")


async def test_render_rejects_unknown_format() -> None:
    service, _, _, _ = _make_service()
    tailored = TailoredCV(
        id=str(uuid4()),
        user_id="user-1",
        source_cv_id=None,
        job_description="JD",
        content="Summary\nExperienced engineer.",
        created_at=datetime.now(UTC),
        sections=[
            TailoredCVSection(id="summary", heading="Summary", body="x", changed=False)
        ],
    )

    with pytest.raises(DomainError):
        await service.render(tailored, format="txt")
