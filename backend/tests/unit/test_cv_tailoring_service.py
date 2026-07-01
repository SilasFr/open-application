"""Unit tests for CVTailoringService against a fake AIClient."""

from __future__ import annotations

import pytest

from app.domain.exceptions import DomainError
from app.services.cv_tailoring_service import CVTailoringService
from tests.fakes import FakeAIClient

TEMPLATE = "CV:\n{{CV}}\n\nJD:\n{{JOB_DESCRIPTION}}"


async def test_tailor_fills_template_and_returns_content() -> None:
    ai = FakeAIClient(response="# Result")
    service = CVTailoringService(ai, TEMPLATE)

    result = await service.tailor(
        user_id="user-1",
        cv_text="Jane Doe, Python engineer",
        job_description="Seeking a Python engineer",
    )

    assert result.content == "# Result"
    assert result.user_id == "user-1"
    # The template placeholders were substituted before hitting the client.
    assert ai.last_prompt is not None
    assert "Jane Doe, Python engineer" in ai.last_prompt
    assert "Seeking a Python engineer" in ai.last_prompt
    assert "{{CV}}" not in ai.last_prompt


async def test_empty_cv_raises() -> None:
    service = CVTailoringService(FakeAIClient(), TEMPLATE)

    with pytest.raises(DomainError):
        await service.tailor(user_id="u", cv_text="   ", job_description="JD")


async def test_empty_job_description_raises() -> None:
    service = CVTailoringService(FakeAIClient(), TEMPLATE)

    with pytest.raises(DomainError):
        await service.tailor(user_id="u", cv_text="CV", job_description="")
