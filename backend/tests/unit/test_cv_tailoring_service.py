"""Unit tests for CVTailoringService against fakes (no network).

The service makes three focused AI calls (contact / prose / experience); tests
drive them with ``RoutingFakeAIClient``, which returns a per-task canned response
by matching a marker in each prompt. Error-path tests use ``FakeAIClient``, which
returns the same response to every call (so all three sub-calls fail together).
"""

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
from app.services.cv_tailoring_service import CVTailoringService, TailoringPrompts
from tests.fakes import (
    DEFAULT_PROSE_RESPONSE,
    FakeAIClient,
    InMemoryApplicationRepository,
    InMemoryCVRepository,
    InMemoryTailoredCVRepository,
    RoutingFakeAIClient,
)

# Minimal test templates: each carries the routing marker RoutingFakeAIClient
# keys on ("contact header" / "prose sections" / "Experience and Education") plus
# the placeholders the service substitutes.
_CONTACT_TEMPLATE = "Extract the contact header.\nCV:\n{{CV}}"
_PROSE_TEMPLATE = (
    "Tailor the prose sections.\nCV:\n{{CV}}\nJD:\n{{JOB_DESCRIPTION}}\n"
    "PREVIOUS:\n{{PREVIOUS_TAILORED_CV}}\nREFINE:\n{{REFINEMENT_INSTRUCTIONS}}"
)
_EXPERIENCE_TEMPLATE = (
    "Tailor the Experience and Education.\nCV:\n{{CV}}\nJD:\n{{JOB_DESCRIPTION}}\n"
    "PREVIOUS:\n{{PREVIOUS_TAILORED_CV}}\nREFINE:\n{{REFINEMENT_INSTRUCTIONS}}"
)
_PROMPTS = TailoringPrompts(
    contact=_CONTACT_TEMPLATE, prose=_PROSE_TEMPLATE, experience=_EXPERIENCE_TEMPLATE
)


def _make_service(
    ai_client: AIClient | None = None,
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
        ai_client or RoutingFakeAIClient(),
        _PROMPTS,
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


async def test_tailor_assembles_contact_prose_and_entries() -> None:
    ai = RoutingFakeAIClient()
    service, cv_repository, _, _ = _make_service(ai)
    await _seed_base_resume(cv_repository, "user-1")

    result = await service.tailor(
        user_id="user-1", job_description="Seeking a Python engineer"
    )

    assert result.user_id == "user-1"
    assert result.contact is not None
    assert result.contact.name == "Jane Doe"
    # summary + skills (prose) + experience (entries), canonically ordered.
    assert [s.id for s in result.sections] == ["summary", "skills", "experience"]
    summary = result.sections[0]
    assert summary.changed is True
    assert summary.explanation
    assert summary.body
    assert not summary.entries
    experience = result.sections[2]
    assert experience.body is None
    assert experience.entries[0].title == "Software Engineer"
    assert experience.entries[0].bullets
    # Entry content is flattened into the stored plain-text content too.
    assert "Summary" in result.content
    assert "Software Engineer" in result.content
    # CV + JD were substituted into the prose sub-call's prompt.
    prose_prompt = ai.prompts["prose"]
    assert "Jane Doe, Python engineer" in prose_prompt
    assert "Seeking a Python engineer" in prose_prompt
    assert "{{CV}}" not in prose_prompt


async def test_sections_are_ordered_canonically() -> None:
    # experience call returns education before experience, and a fictional extra
    # section — assembly must still order summary, skills, experience, education,
    # with unknown ids appended.
    experience_response = json.dumps(
        {
            "sections": [
                {
                    "id": "education",
                    "heading": "Education",
                    "changed": False,
                    "entries": [{"title": "BSc CS", "organization": "Uni"}],
                    "explanation": None,
                },
                {
                    "id": "experience",
                    "heading": "Experience",
                    "changed": False,
                    "entries": [{"title": "Engineer"}],
                    "explanation": None,
                },
                {
                    "id": "projects",
                    "heading": "Projects",
                    "changed": False,
                    "entries": [{"title": "Side project"}],
                    "explanation": None,
                },
            ]
        }
    )
    ai = RoutingFakeAIClient(experience=experience_response)
    service, cv_repository, _, _ = _make_service(ai)
    await _seed_base_resume(cv_repository, "user-1")

    result = await service.tailor(user_id="user-1", job_description="JD")

    assert [s.id for s in result.sections] == [
        "summary",
        "skills",
        "experience",
        "education",
        "projects",
    ]


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
    """A vendor SDK failure (auth, rate limit, network, outage — modeled as a
    generic RuntimeError since the service must not depend on any provider's
    exception types) surfaces as a clean, retryable AIGenerationError."""
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


async def test_retries_once_on_malformed_sub_call_then_succeeds() -> None:
    # The prose sub-call is malformed on its first attempt, valid on the second —
    # tailor() should recover rather than surface an error.
    ai = RoutingFakeAIClient(prose=["null, not json", DEFAULT_PROSE_RESPONSE])
    service, cv_repository, _, _ = _make_service(ai)
    await _seed_base_resume(cv_repository, "user-1")

    result = await service.tailor(user_id="user-1", job_description="JD")

    assert result.sections
    assert ai.calls["prose"] == 2  # exactly one retry on the prose call
    assert ai.calls["contact"] == 1  # other calls succeeded first try
    assert ai.calls["experience"] == 1


async def test_gives_up_after_max_attempts_on_persistent_malformed_sub_call() -> None:
    ai = RoutingFakeAIClient(experience=["bad one", "bad two", "bad three", "bad four"])
    service, cv_repository, _, _ = _make_service(ai)
    await _seed_base_resume(cv_repository, "user-1")

    with pytest.raises(InvalidAIResponseError):
        await service.tailor(user_id="user-1", job_description="JD")
    assert ai.calls["experience"] == 3  # bounded — no infinite retry


async def test_prose_call_missing_sections_key_raises() -> None:
    ai = RoutingFakeAIClient(prose=json.dumps({"not_sections": []}))
    service, cv_repository, _, _ = _make_service(ai)
    await _seed_base_resume(cv_repository, "user-1")

    with pytest.raises(InvalidAIResponseError):
        await service.tailor(user_id="user-1", job_description="JD")


async def test_prose_call_empty_sections_list_raises() -> None:
    ai = RoutingFakeAIClient(prose=json.dumps({"sections": []}))
    service, cv_repository, _, _ = _make_service(ai)
    await _seed_base_resume(cv_repository, "user-1")

    with pytest.raises(InvalidAIResponseError):
        await service.tailor(user_id="user-1", job_description="JD")


async def test_prose_section_missing_body_raises() -> None:
    ai = RoutingFakeAIClient(
        prose=json.dumps(
            {
                "sections": [
                    {"id": "summary", "heading": "Summary", "changed": False}
                ]
            }
        )
    )
    service, cv_repository, _, _ = _make_service(ai)
    await _seed_base_resume(cv_repository, "user-1")

    with pytest.raises(InvalidAIResponseError):
        await service.tailor(user_id="user-1", job_description="JD")


async def test_experience_section_empty_entries_raises() -> None:
    ai = RoutingFakeAIClient(
        experience=json.dumps(
            {
                "sections": [
                    {
                        "id": "experience",
                        "heading": "Experience",
                        "changed": False,
                        "entries": [],
                        "explanation": None,
                    }
                ]
            }
        )
    )
    service, cv_repository, _, _ = _make_service(ai)
    await _seed_base_resume(cv_repository, "user-1")

    with pytest.raises(InvalidAIResponseError):
        await service.tailor(user_id="user-1", job_description="JD")


async def test_changed_section_without_explanation_raises() -> None:
    ai = RoutingFakeAIClient(
        prose=json.dumps(
            {
                "sections": [
                    {
                        "id": "summary",
                        "heading": "Summary",
                        "body": "...",
                        "changed": True,
                        "explanation": None,
                    }
                ]
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


async def test_refinement_threads_previous_content_into_prose_and_experience() -> None:
    ai = RoutingFakeAIClient()
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
    # The prior content and the instruction reach both tailoring sub-calls...
    for task in ("prose", "experience"):
        assert "Keep it to one page." in ai.prompts[task]
        assert first.content in ai.prompts[task]
    # ...but not the contact call, which is pure extraction (CV only).
    assert "Keep it to one page." not in ai.prompts["contact"]


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
