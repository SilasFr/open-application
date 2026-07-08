"""Fixtures for API tests: a TestClient with fakes injected via dependency overrides."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.dependencies import (
    get_application_service,
    get_contact_service,
    get_cv_service,
    get_cv_tailoring_service,
    get_note_service,
    get_task_service,
)
from app.core.security import get_current_user_id
from app.main import create_app
from app.services.application_service import ApplicationService
from app.services.contact_service import ContactService
from app.services.cv_service import CVService
from app.services.cv_tailoring_service import CVTailoringService, TailoringPrompts
from app.services.note_service import NoteService
from app.services.task_service import TaskService
from tests.fakes import (
    InMemoryApplicationRepository,
    InMemoryContactRepository,
    InMemoryCVRepository,
    InMemoryNoteRepository,
    InMemoryTailoredCVRepository,
    InMemoryTaskRepository,
    RoutingFakeAIClient,
)

# Markered per-shape templates so RoutingFakeAIClient routes each of the three
# sub-calls to its own valid canned response. Exported for the standalone
# malformed-response test.
TEST_PROMPTS = TailoringPrompts(
    contact="Extract the contact header.\nCV:\n{{CV}}",
    prose=(
        "Tailor the prose sections.\nCV:\n{{CV}}\nJD:\n{{JOB_DESCRIPTION}}\n"
        "PREVIOUS:\n{{PREVIOUS_TAILORED_CV}}\nREFINE:\n{{REFINEMENT_INSTRUCTIONS}}"
    ),
    experience=(
        "Tailor the Experience and Education.\nCV:\n{{CV}}\nJD:\n{{JOB_DESCRIPTION}}\n"
        "PREVIOUS:\n{{PREVIOUS_TAILORED_CV}}\nREFINE:\n{{REFINEMENT_INSTRUCTIONS}}"
    ),
)
_TEST_USER_ID = "user-api"


def _override_services(app: FastAPI) -> None:
    """Inject in-memory service implementations so tests need no network."""
    repository = InMemoryApplicationRepository()
    note_repository = InMemoryNoteRepository()
    contact_repository = InMemoryContactRepository()
    task_repository = InMemoryTaskRepository()
    cv_repository = InMemoryCVRepository()
    tailored_repository = InMemoryTailoredCVRepository()

    app.dependency_overrides[get_application_service] = lambda: ApplicationService(
        repository, note_repository
    )
    app.dependency_overrides[get_note_service] = lambda: NoteService(
        note_repository, repository
    )
    app.dependency_overrides[get_contact_service] = lambda: ContactService(
        contact_repository, repository
    )
    app.dependency_overrides[get_task_service] = lambda: TaskService(
        task_repository, repository
    )
    app.dependency_overrides[get_cv_service] = lambda: CVService(cv_repository)
    app.dependency_overrides[get_cv_tailoring_service] = lambda: CVTailoringService(
        RoutingFakeAIClient(), TEST_PROMPTS, cv_repository, tailored_repository, repository
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
