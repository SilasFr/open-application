"""Business logic for AI-powered, structured CV tailoring.

The tailoring is decomposed into three focused AI calls, each producing one
unambiguous JSON shape: the contact header, the prose sections (summary/skills),
and the structured experience/education entries. Splitting by shape removes the
body-vs-entries ambiguity a single combined call created — smaller models were
conflating the two (e.g. emitting skills as ``entries``). The three calls are
independent and run concurrently; the service assembles and orders the result
into a single ``TailoredCV`` (output shape unchanged for the rest of the app).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal, TypeVar
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

# Placeholders substituted into the versioned prompt templates.
_CV_PLACEHOLDER = "{{CV}}"
_JD_PLACEHOLDER = "{{JOB_DESCRIPTION}}"
_PREVIOUS_PLACEHOLDER = "{{PREVIOUS_TAILORED_CV}}"
_REFINEMENT_PLACEHOLDER = "{{REFINEMENT_INSTRUCTIONS}}"

_NONE_PLACEHOLDER_TEXT = "(none)"

# Total attempts to get valid structured output before giving up. Smaller models
# glitch on a required field ~10% of the time; at 3 attempts the compounded
# failure rate is ~0.1%, and the extra calls are only paid on the rare failure
# path. Applied per sub-call.
_MAX_GENERATION_ATTEMPTS = 3

# Canonical section order for assembly, regardless of which call produced each.
_SECTION_ORDER = {"summary": 0, "skills": 1, "experience": 2, "education": 3}

_logger = logging.getLogger(__name__)

_ModelT = TypeVar("_ModelT", bound=BaseModel)


@dataclass(frozen=True)
class TailoringPrompts:
    """The three versioned prompt templates the tailoring pipeline uses, loaded
    at the composition root and injected so this class knows no filesystem."""

    contact: str
    prose: str
    experience: str


class _ContactLinkModel(BaseModel):
    """A labelled URL in the CV header.

    ``url`` is nullable: text extraction from a PDF often yields a link's visible
    label ("LinkedIn Profile") without its underlying href, and the model — told
    not to invent details — returns a null URL. Such links are dropped during
    assembly rather than failing the whole tailor.
    """

    label: str
    url: str | None = None


class _ContactModel(BaseModel):
    """Header/contact details extracted from the base resume."""

    name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    links: list[_ContactLinkModel] = Field(default_factory=list)


class _ContactResult(BaseModel):
    """Output of the contact-extraction call."""

    contact: _ContactModel


class _EntryModel(BaseModel):
    """A structured item within a section (a role, degree, etc.)."""

    title: str
    organization: str | None = None
    date_range: str | None = None
    context: str | None = None
    bullets: list[str] = Field(default_factory=list)


def _require_changed_have_explanation(sections: list[_HasChangeMeta]) -> None:
    for section in sections:
        if section.changed and not (section.explanation or "").strip():
            raise ValueError(
                f"section '{section.id}' is changed but has no explanation"
            )


class _HasChangeMeta(BaseModel):
    """Fields shared by both section shapes (used by the explanation check)."""

    id: str
    heading: str
    changed: bool
    explanation: str | None = None


class _ProseSectionModel(_HasChangeMeta):
    """A prose section (summary/skills): content is a single ``body`` string.

    There is deliberately no ``entries`` field — this call cannot produce
    structured entries, which is what removes the body-vs-entries ambiguity.
    """

    body: str = Field(min_length=1)


class _EntrySectionModel(_HasChangeMeta):
    """A structured section (experience/education): content is ``entries``.

    There is deliberately no ``body`` field on this shape.
    """

    entries: list[_EntryModel] = Field(min_length=1)


class _ProseSectionsResult(BaseModel):
    """Output of the prose-sections call."""

    sections: list[_ProseSectionModel] = Field(min_length=1)

    @model_validator(mode="after")
    def _changed_sections_require_explanation(self) -> _ProseSectionsResult:
        _require_changed_have_explanation(list(self.sections))
        return self


class _EntrySectionsResult(BaseModel):
    """Output of the experience/education call."""

    sections: list[_EntrySectionModel] = Field(min_length=1)

    @model_validator(mode="after")
    def _changed_sections_require_explanation(self) -> _EntrySectionsResult:
        _require_changed_have_explanation(list(self.sections))
        return self


class CVTailoringService:
    """Turns a saved base CV plus a job description into a tailored CV via three
    focused AIClient calls, persisting the assembled structured result.

    Refinement reuses the same pipeline: the prior tailored content and the
    instructions are threaded into the prose and experience prompts.
    """

    def __init__(
        self,
        ai_client: AIClient,
        prompts: TailoringPrompts,
        cv_repository: CVRepository,
        tailored_repository: TailoredCVRepository,
        application_repository: ApplicationRepository,
    ) -> None:
        self._ai_client = ai_client
        self._prompts = prompts
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

        cv_text = base_resume.content or ""
        contact_prompt = self._prompts.contact.replace(_CV_PLACEHOLDER, cv_text)
        prose_prompt = self._build_prompt(
            self._prompts.prose,
            cv_text=cv_text,
            job_description=jd.text,
            previous=previous,
            refinement_instructions=refinement_instructions,
        )
        experience_prompt = self._build_prompt(
            self._prompts.experience,
            cv_text=cv_text,
            job_description=jd.text,
            previous=previous,
            refinement_instructions=refinement_instructions,
        )

        # The three calls are independent, but we run them sequentially rather
        # than concurrently: free-tier hosted providers (e.g. Groq) enforce a
        # tokens-per-minute limit, and firing all three at once bursts past it
        # (HTTP 429). Sequential calls spread the load and stay within the limit;
        # each provider is fast enough that total latency is still a few seconds.
        # The first failure (after its retries) short-circuits and propagates,
        # mapped to 422/502 at the API boundary.
        contact_result = await self._generate_json(
            contact_prompt, _ContactResult, "contact"
        )
        prose_result = await self._generate_json(
            prose_prompt, _ProseSectionsResult, "prose"
        )
        experience_result = await self._generate_json(
            experience_prompt, _EntrySectionsResult, "experience"
        )

        contact = self._to_contact(contact_result.contact)
        sections = self._assemble_sections(prose_result, experience_result)
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

    @staticmethod
    def _build_prompt(
        template: str,
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
            template.replace(_CV_PLACEHOLDER, cv_text)
            .replace(_JD_PLACEHOLDER, job_description)
            .replace(_PREVIOUS_PLACEHOLDER, previous_text)
            .replace(_REFINEMENT_PLACEHOLDER, refinement_text)
        )

    async def _generate_json(
        self, prompt: str, validator: type[_ModelT], label: str
    ) -> _ModelT:
        """Generate + validate one sub-call's JSON, retrying on malformed output.

        A malformed response (bad JSON or failed validation) is a transient
        small-model glitch and is retried up to ``_MAX_GENERATION_ATTEMPTS``. A
        hard provider failure (auth/rate-limit/outage) is not retried here — it
        surfaces immediately as ``AIGenerationError``.
        """

        last_error: InvalidAIResponseError | None = None
        for attempt in range(1, _MAX_GENERATION_ATTEMPTS + 1):
            try:
                raw_response = await self._ai_client.generate(
                    system=_SYSTEM_PROMPT, prompt=prompt
                )
            except Exception as exc:
                # Deliberately broad: the AIClient may be backed by any vendor
                # SDK with its own exception hierarchy. The service must not
                # special-case any of them (Principle III/V) — it only guarantees
                # the caller sees a clean, retryable error rather than a 500.
                _logger.exception("AI generation failed (%s)", label)
                raise AIGenerationError(
                    "AI tailoring is temporarily unavailable. Please try again."
                ) from exc

            try:
                return self._parse_json(raw_response, validator)
            except InvalidAIResponseError as exc:
                last_error = exc
                _logger.warning(
                    "AI structured-output validation failed for %s "
                    "(attempt %d/%d): %s",
                    label,
                    attempt,
                    _MAX_GENERATION_ATTEMPTS,
                    exc,
                )

        assert last_error is not None  # loop runs at least once
        raise last_error

    @staticmethod
    def _parse_json(raw_response: str, validator: type[_ModelT]) -> _ModelT:
        try:
            data = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise InvalidAIResponseError("AI response was not valid JSON") from exc
        try:
            return validator.model_validate(data)
        except ValidationError as exc:
            raise InvalidAIResponseError(
                f"AI response failed structured-output validation: {exc}"
            ) from exc

    @staticmethod
    def _to_contact(contact: _ContactModel) -> TailoredCVContact:
        return TailoredCVContact(
            name=contact.name,
            email=contact.email,
            phone=contact.phone,
            location=contact.location,
            # Drop links whose URL wasn't present in the CV — a label with no
            # href isn't a usable link.
            links=[
                ContactLink(label=link.label, url=link.url)
                for link in contact.links
                if link.url and link.url.strip()
            ],
        )

    @staticmethod
    def _assemble_sections(
        prose: _ProseSectionsResult, experience: _EntrySectionsResult
    ) -> list[TailoredCVSection]:
        """Merge the two calls' sections into one canonically-ordered list."""

        sections: list[TailoredCVSection] = []
        for prose_section in prose.sections:
            sections.append(
                TailoredCVSection(
                    id=prose_section.id,
                    heading=prose_section.heading,
                    changed=prose_section.changed,
                    body=prose_section.body,
                    entries=[],
                    explanation=prose_section.explanation,
                )
            )
        for entry_section in experience.sections:
            sections.append(
                TailoredCVSection(
                    id=entry_section.id,
                    heading=entry_section.heading,
                    changed=entry_section.changed,
                    body=None,
                    entries=[
                        TailoredCVEntry(
                            title=entry.title,
                            organization=entry.organization,
                            date_range=entry.date_range,
                            context=entry.context,
                            bullets=list(entry.bullets),
                        )
                        for entry in entry_section.entries
                    ],
                    explanation=entry_section.explanation,
                )
            )
        sections.sort(key=lambda s: _SECTION_ORDER.get(s.id, len(_SECTION_ORDER)))
        return sections

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
                    header = (
                        f"{header} ({entry.date_range})" if header else entry.date_range
                    )
                if header:
                    lines.append(header)
                lines.extend(f"- {bullet}" for bullet in entry.bullets)
            blocks.append("\n".join(lines))
        return "\n\n".join(blocks)
