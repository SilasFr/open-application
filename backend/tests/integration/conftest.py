"""Fixtures for API tests: a TestClient with fakes injected via dependency overrides."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.dependencies import get_application_service, get_cv_tailoring_service
from app.main import create_app
from app.services.application_service import ApplicationService
from app.services.cv_tailoring_service import CVTailoringService
from tests.fakes import FakeAIClient, InMemoryApplicationRepository

_PROMPT = "CV:\n{{CV}}\n\nJD:\n{{JOB_DESCRIPTION}}"


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app()

    repository = InMemoryApplicationRepository()
    app.dependency_overrides[get_application_service] = lambda: ApplicationService(
        repository
    )
    app.dependency_overrides[get_cv_tailoring_service] = lambda: CVTailoringService(
        FakeAIClient(response="# Tailored"), _PROMPT
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
