"""Fixtures for API tests: a TestClient with fakes injected via dependency overrides."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.dependencies import (
    get_application_service,
    get_cv_tailoring_service,
    get_note_service,
)
from app.core.security import get_current_user_id
from app.main import create_app
from app.services.application_service import ApplicationService
from app.services.cv_tailoring_service import CVTailoringService
from app.services.note_service import NoteService
from tests.fakes import (
    FakeAIClient,
    InMemoryApplicationRepository,
    InMemoryNoteRepository,
)

_PROMPT = "CV:\n{{CV}}\n\nJD:\n{{JOB_DESCRIPTION}}"
_TEST_USER_ID = "user-api"


def _override_services(app: FastAPI) -> None:
    """Inject in-memory service implementations so tests need no network."""
    repository = InMemoryApplicationRepository()
    note_repository = InMemoryNoteRepository()
    app.dependency_overrides[get_application_service] = lambda: ApplicationService(
        repository, note_repository
    )
    app.dependency_overrides[get_note_service] = lambda: NoteService(
        note_repository, repository
    )
    app.dependency_overrides[get_cv_tailoring_service] = lambda: CVTailoringService(
        FakeAIClient(response="# Tailored"), _PROMPT
    )


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Authenticated client: auth is stubbed to a fixed user so tests can focus
    on routing and business logic."""
    app = create_app()
    _override_services(app)
    app.dependency_overrides[get_current_user_id] = lambda: _TEST_USER_ID

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def unauthed_client() -> Iterator[TestClient]:
    """Client with REAL auth (services still faked) — for testing 401 behavior."""
    app = create_app()
    _override_services(app)

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
