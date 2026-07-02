"""Unit tests for ContactService against in-memory repositories."""

from __future__ import annotations

import pytest

from app.domain.exceptions import NotFoundError
from app.services.application_service import ApplicationService
from app.services.contact_service import ContactService
from tests.fakes import (
    InMemoryApplicationRepository,
    InMemoryContactRepository,
    InMemoryNoteRepository,
)

USER = "user-1"
OTHER_USER = "user-2"


async def _setup() -> tuple[ContactService, str]:
    """Return a ContactService plus an application id owned by USER."""
    applications = InMemoryApplicationRepository()
    app_service = ApplicationService(applications, InMemoryNoteRepository())
    application = await app_service.create(user_id=USER, company="Acme", role="Engineer")
    return ContactService(InMemoryContactRepository(), applications), application.id


async def test_create_and_list() -> None:
    service, application_id = await _setup()

    await service.create(
        user_id=USER,
        application_id=application_id,
        name="Jane Recruiter",
        role="Recruiter",
        email="jane@example.com",
    )

    listed = await service.list(USER, application_id)
    assert len(listed) == 1
    assert listed[0].name == "Jane Recruiter"
    assert listed[0].role == "Recruiter"


async def test_create_rejects_unowned_application() -> None:
    service, application_id = await _setup()

    with pytest.raises(NotFoundError):
        await service.create(
            user_id=OTHER_USER, application_id=application_id, name="x"
        )


async def test_update_partial_fields() -> None:
    service, application_id = await _setup()
    contact = await service.create(
        user_id=USER, application_id=application_id, name="Jane"
    )

    updated = await service.update(
        USER, application_id, contact.id, linkedin_url="https://linkedin.com/in/jane"
    )

    assert updated.name == "Jane"
    assert updated.linkedin_url == "https://linkedin.com/in/jane"


async def test_update_missing_contact_raises() -> None:
    service, application_id = await _setup()

    with pytest.raises(NotFoundError):
        await service.update(USER, application_id, "does-not-exist", name="x")


async def test_delete_then_list_empty() -> None:
    service, application_id = await _setup()
    contact = await service.create(
        user_id=USER, application_id=application_id, name="Jane"
    )

    await service.delete(USER, application_id, contact.id)

    assert await service.list(USER, application_id) == []


async def test_delete_rejects_unowned_application() -> None:
    service, application_id = await _setup()
    contact = await service.create(
        user_id=USER, application_id=application_id, name="Jane"
    )

    with pytest.raises(NotFoundError):
        await service.delete(OTHER_USER, application_id, contact.id)
