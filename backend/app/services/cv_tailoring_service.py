"""Business logic for AI-powered, structured CV tailoring."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

import anyio
from pydantic import BaseModel, Field, ValidationError, model_validator

from app.domain.ai import AIClient
from app.domain.entities import (
    ContactLink,
    TailoredCV,
    TailoredCVContact,
    TailoredCVEntry,
    TailoredCVSection,
)
from app.domain.exceptions import (
    AIGenerationError,
    BaseResumeNotFoundError,
    DomainError,
    InvalidAIResponseError,
    NotFoundError,
)
from app.domain.repositories import (
    ApplicationRepository,
    CVRepository,
    TailoredCVRepository,
)
from app.domain.value_objects import JobDescription
from app.infrastructure.cv_document_rendering import (
    DOCX_CONTENT_TYPE,
    PDF_CONTENT_TYPE,
    render_docx,
    render_pdf,
)

_SYSTEM_PROMPT = (
    "You are an expert career coach and professional CV writer. You tailor a "
    "candidate's existing CV to a specific job description, keeping every claim "
    "truthful and grounded in the original CV. Never invent experience. You "
    "always respond with the exact JSON shape requested, nothing else."
)

# Placeholders substituted into the versioned prompt template.
_CV_PLACEHOLDER = "{{CV}}"
_JD_PLACEHOLDER = "{{JOB_DESCRIPTION}}"
_PREVIOUS_PLACEHOLDER = "{{PREVIOUS_TAILORED_CV}}"
_REFINEMENT_PLACEHOLDER = "{{REFINEMENT_INSTRUCTIONS}}"

_NONE_PLACEHOLDER_TEXT = "(none)"

# Total attempts to get valid structured output before giving up. Smaller models
# glitch on a required field ~10% of the time (measured, qwen2.5:7b); at 3
# attempts the compounded failure rate is ~0.1%, and the extra calls are only
# ever paid on the rare failure path.
_MAX_GENERATION_ATTEMPTS = 3

_logger = logging.getLogger(__name__)


class _ContactLinkModel(BaseModel):
    """A labelled URL in the CV header."""

    label: str
    url: str


class _ContactModel(BaseModel):
    """Header/contact details extracted from the base resume."""

    name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    links: list[_ContactLinkModel] = Field(default_factory=list)


class _EntryModel(BaseModel):
    """A structured item within a section (a role, degree, etc.)."""

    title: str
    organization: str | None = None
    date_range: str | None = None
    context: str | None = None
    bullets: list[str] = Field(default_factory=list)


class _SectionModel(BaseModel):
    """Validates a single section of the AI's structured JSON response.

    A section renders from either ``body`` (prose) or ``entries`` (structured);
    at least one must be present and non-empty.
    """

    id: str
    heading: str
    changed: bool
    body: str | None = None
    entries: list[_EntryModel] = Field(default_factory=list)
    explanation: str | None = None

    @model_validator(mode="after")
    def _requires_body_or_entries(self) -> _SectionModel:
        if not (self.body or "").strip() and not self.entries:
            raise ValueError(
                f"section '{self.id}' has neither body text nor entries"
            )
        return self


class _StructuredOutputModel(BaseModel):
    """Validates the AI's full structured JSON response: a contact header plus a
    non-empty sections list; every changed section has a non-null explanation."""

    contact: _ContactModel
    sections: list[_SectionModel] = Field(min_length=1)

    @model_validator(mode="after")
    def _changed_sections_require_explanation(self) -> _StructuredOutputModel:
        for section in self.sections:
            if section.changed and not (section.explanation or "").strip():
                raise ValueError(
                    f"section '{section.id}' is changed but has no explanation"
                )
        return self


class CVTailoringService:
    """Turns a saved base CV plus a job description into a tailored CV via the
    AIClient, persisting the structured result.

    The prompt template is injected (loaded from a versioned file at the
    composition root), so this class has no knowledge of the filesystem or vendor.
    Refinement (research.md #6) reuses this same operation: it's the same
    generation + structured-output validation, with extra prior-content context.
    """

    def __init__(
        self,
        ai_client: AIClient,
        prompt_template: str,
        cv_repository: CVRepository,
        tailored_repository: TailoredCVRepository,
        application_repository: ApplicationRepository,
    ) -> None:
        self._ai_client = ai_client
        self._prompt_template = prompt_template
        self._cv_repository = cv_repository
        self._tailored_repository = tailored_repository
        self._application_repository = application_repository

    async def tailor(
        self,
        *,
        user_id: str,
        job_description: str,
        refinement_instructions: str | None = None,
        previous_tailored_cv_id: str | None = None,
    ) -> TailoredCV:
        jd = JobDescription(job_description)
        if jd.is_empty():
            raise DomainError("job_description must not be empty")
        if refinement_instructions is not None and not refinement_instructions.strip():
            raise DomainError("refinement_instructions must not be empty")

        base_resume = await self._cv_repository.get_current(user_id)
        if base_resume is None or not (base_resume.content or "").strip():
            raise BaseResumeNotFoundError("No base resume saved for this user")

        previous: TailoredCV | None = None
        if previous_tailored_cv_id is not None:
            previous = await self._tailored_repository.get(
                user_id, previous_tailored_cv_id
            )
            if previous is None:
                raise NotFoundError(f"Tailored CV {previous_tailored_cv_id} not found")

        prompt = self._build_prompt(
            cv_text=base_resume.content or "",
            job_description=jd.text,
            previous=previous,
            refinement_instructions=refinement_instructions,
        )
        contact, sections = await self._generate_structured(prompt)
        content = self._render_plain_text(sections)

        tailored = TailoredCV(
            id=str(uuid4()),
            user_id=user_id,
            source_cv_id=base_resume.id,
            job_description=jd.text,
            content=content,
            created_at=datetime.now(UTC),
            contact=contact,
            sections=sections,
            application_id=None,
            refinement_instructions=refinement_instructions,
            previous_tailored_cv_id=previous_tailored_cv_id,
        )
        return await self._tailored_repository.add(tailored)

    async def get_owned(self, user_id: str, tailored_id: str) -> TailoredCV:
        tailored = await self._tailored_repository.get(user_id, tailored_id)
        if tailored is None:
            raise NotFoundError(f"Tailored CV {tailored_id} not found")
        return tailored

    async def attach(
        self, user_id: str, tailored_id: str, application_id: str
    ) -> TailoredCV:
        tailored = await self.get_owned(user_id, tailored_id)
        application = await self._application_repository.get(user_id, application_id)
        if application is None:
            raise NotFoundError(f"Application {application_id} not found")
        tailored.application_id = application_id
        return await self._tailored_repository.update(tailored)

    async def render(
        self, tailored: TailoredCV, *, format: str
    ) -> tuple[bytes, str, str]:
        """Render ``tailored`` as a downloadable document.

        Returns ``(bytes, content_type, filename)``. Raises ``DomainError`` (maps
        to HTTP 400) for an unrecognized ``format``.

        PDF/DOCX generation is CPU-bound (reportlab / python-docx), so it's
        offloaded to a worker thread — same ``anyio.to_thread.run_sync`` pattern
        the Supabase repositories use — to keep the event loop unblocked.
        """

        fmt: Literal["pdf", "docx"]
        if format == "pdf":
            fmt = "pdf"
            data = await anyio.to_thread.run_sync(render_pdf, tailored)
            content_type = PDF_CONTENT_TYPE
        elif format == "docx":
            fmt = "docx"
            data = await anyio.to_thread.run_sync(render_docx, tailored)
            content_type = DOCX_CONTENT_TYPE
        else:
            raise DomainError(f"Unsupported download format: {format!r}")
        return data, content_type, f"tailored-cv.{fmt}"

    def _build_prompt(
        self,
        *,
        cv_text: str,
        job_description: str,
        previous: TailoredCV | None,
        refinement_instructions: str | None,
    ) -> str:
        previous_text = (
            previous.content if previous is not None else _NONE_PLACEHOLDER_TEXT
        )
        refinement_text = (
            refinement_instructions
            if refinement_instructions
            else _NONE_PLACEHOLDER_TEXT
        )
        return (
            self._prompt_template.replace(_CV_PLACEHOLDER, cv_text)
            .replace(_JD_PLACEHOLDER, job_description)
            .replace(_PREVIOUS_PLACEHOLDER, previous_text)
            .replace(_REFINEMENT_PLACEHOLDER, refinement_text)
        )

    async def _generate_structured(
        self, prompt: str
    ) -> tuple[TailoredCVContact, list[TailoredCVSection]]:
        """Generate + validate the structured output, retrying once on malformed
        output.

        Smaller/open models occasionally emit a structurally-invalid object (e.g.
        a null on a required field) — a transient, non-deterministic glitch, not
        a persistent failure. One retry with the same prompt turns a ~10% failure
        rate into ~1% and is provider-agnostic (all `AIClient`s benefit). A hard
        provider failure (auth/rate-limit/outage) is not a parse error and is not
        retried here — it surfaces immediately as ``AIGenerationError``.
        """

        last_error: InvalidAIResponseError | None = None
        for attempt in range(1, _MAX_GENERATION_ATTEMPTS + 1):
            try:
                raw_response = await self._ai_client.generate(
                    system=_SYSTEM_PROMPT, prompt=prompt
                )
            except Exception as exc:
                # Deliberately broad: the AIClient abstraction may be backed by any
                # vendor SDK, each with its own exception hierarchy (auth errors,
                # rate limits, network failures, outages). The service must not
                # import or special-case any of them (Principle III/V) — it only
                # needs to guarantee the caller sees a clean, retryable error
                # instead of an unhandled 500 (spec.md Edge Cases: generation
                # failure must be retryable without losing the job description or
                # base resume — the frontend keeps both on error).
                _logger.exception("AI generation failed")
                raise AIGenerationError(
                    "AI tailoring is temporarily unavailable. Please try again."
                ) from exc

            try:
                return self._parse_structured(raw_response)
            except InvalidAIResponseError as exc:
                last_error = exc
                _logger.warning(
                    "AI structured-output validation failed (attempt %d/%d): %s",
                    attempt,
                    _MAX_GENERATION_ATTEMPTS,
                    exc,
                )

        # Every attempt produced malformed output — surface the last failure.
        assert last_error is not None  # loop runs at least once
        raise last_error

    @staticmethod
    def _parse_structured(
        raw_response: str,
    ) -> tuple[TailoredCVContact, list[TailoredCVSection]]:
        try:
            data = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise InvalidAIResponseError("AI response was not valid JSON") from exc

        try:
            parsed = _StructuredOutputModel.model_validate(data)
        except ValidationError as exc:
            raise InvalidAIResponseError(
                f"AI response failed structured-output validation: {exc}"
            ) from exc

        contact = TailoredCVContact(
            name=parsed.contact.name,
            email=parsed.contact.email,
            phone=parsed.contact.phone,
            location=parsed.contact.location,
            links=[
                ContactLink(label=link.label, url=link.url)
                for link in parsed.contact.links
            ],
        )
        sections = [
            TailoredCVSection(
                id=section.id,
                heading=section.heading,
                changed=section.changed,
                body=section.body,
                entries=[
                    TailoredCVEntry(
                        title=entry.title,
                        organization=entry.organization,
                        date_range=entry.date_range,
                        context=entry.context,
                        bullets=list(entry.bullets),
                    )
                    for entry in section.entries
                ],
                explanation=section.explanation,
            )
            for section in parsed.sections
        ]
        return contact, sections

    @staticmethod
    def _render_plain_text(sections: list[TailoredCVSection]) -> str:
        """Flatten sections to plain text for the stored ``content`` field
        (search/preview) — the styled document is rendered separately."""

        blocks: list[str] = []
        for section in sections:
            lines = [section.heading]
            if section.body:
                lines.append(section.body)
            for entry in section.entries:
                header = " — ".join(
                    part for part in (entry.title, entry.organization) if part
                )
                if entry.date_range:
                    header = f"{header} ({entry.date_range})" if header else entry.date_range
                if header:
                    lines.append(header)
                lines.extend(f"- {bullet}" for bullet in entry.bullets)
            blocks.append("\n".join(lines))
        return "\n\n".join(blocks)
