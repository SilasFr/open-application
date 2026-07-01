"""Business logic for AI-powered CV tailoring."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.domain.ai import AIClient
from app.domain.entities import TailoredCV
from app.domain.exceptions import DomainError
from app.domain.value_objects import JobDescription

_SYSTEM_PROMPT = (
    "You are an expert career coach and professional CV writer. You tailor a "
    "candidate's existing CV to a specific job description, keeping every claim "
    "truthful and grounded in the original CV. Never invent experience."
)

# Placeholders substituted into the versioned prompt template.
_CV_PLACEHOLDER = "{{CV}}"
_JD_PLACEHOLDER = "{{JOB_DESCRIPTION}}"


class CVTailoringService:
    """Turns a base CV plus a job description into a tailored CV via the AIClient.

    The prompt template is injected (loaded from a versioned file at the
    composition root), so this class has no knowledge of the filesystem or vendor.
    """

    def __init__(self, ai_client: AIClient, prompt_template: str) -> None:
        self._ai_client = ai_client
        self._prompt_template = prompt_template

    async def tailor(
        self,
        *,
        user_id: str,
        cv_text: str,
        job_description: str,
        source_cv_id: str | None = None,
    ) -> TailoredCV:
        jd = JobDescription(job_description)
        if not cv_text.strip():
            raise DomainError("cv_text must not be empty")
        if jd.is_empty():
            raise DomainError("job_description must not be empty")

        prompt = self._prompt_template.replace(_CV_PLACEHOLDER, cv_text).replace(
            _JD_PLACEHOLDER, jd.text
        )
        content = await self._ai_client.generate(system=_SYSTEM_PROMPT, prompt=prompt)

        return TailoredCV(
            id=str(uuid4()),
            user_id=user_id,
            source_cv_id=source_cv_id,
            job_description=jd.text,
            content=content,
            created_at=datetime.now(UTC),
        )
