"""Unit tests for NoteService against in-memory repositories."""

from __future__ import annotations

import pytest

from app.domain.exceptions import NotFoundError
from app.domain.value_objects import NoteType
from app.services.application_service import ApplicationService
from app.services.note_service import NoteService
from tests.fakes import InMemoryApplicationRepository, InMemoryNoteRepository

USER = "user-1"
OTHER_USER = "user-2"


async def _setup() -> tuple[NoteService, str]:
    """Return a NoteService plus an application id owned by USER."""
    applications = InMemoryApplicationRepository()
    notes = InMemoryNoteRepository()
    app_service = ApplicationService(applications, notes)
    application = await app_service.create(user_id=USER, company="Acme", role="Engineer")
    return NoteService(notes, applications), application.id


async def test_create_and_list_newest_first() -> None:
    service, application_id = await _setup()

    await service.create(user_id=USER, application_id=application_id, content="First")
    await service.create(user_id=USER, application_id=application_id, content="Second")

    listed = await service.list(USER, application_id)
    assert [n.content for n in listed] == ["Second", "First"]
    assert all(n.type is NoteType.NOTE for n in listed)


async def test_create_rejects_unowned_application() -> None:
    service, application_id = await _setup()

    with pytest.raises(NotFoundError):
        await service.create(user_id=OTHER_USER, application_id=application_id, content="x")


async def test_list_rejects_unowned_application() -> None:
    service, application_id = await _setup()

    with pytest.raises(NotFoundError):
        await service.list(OTHER_USER, application_id)


async def test_update_sets_content_and_updated_at() -> None:
    service, application_id = await _setup()
    note = await service.create(
        user_id=USER, application_id=application_id, content="Original"
    )

    updated = await service.update(USER, application_id, note.id, "Edited")

    assert updated.content == "Edited"
    assert updated.updated_at >= note.updated_at


async def test_update_missing_note_raises() -> None:
    service, application_id = await _setup()

    with pytest.raises(NotFoundError):
        await service.update(USER, application_id, "does-not-exist", "x")


async def test_delete_then_list_empty() -> None:
    service, application_id = await _setup()
    note = await service.create(user_id=USER, application_id=application_id, content="x")

    await service.delete(USER, application_id, note.id)

    assert await service.list(USER, application_id) == []


async def test_delete_rejects_unowned_application() -> None:
    service, application_id = await _setup()
    note = await service.create(user_id=USER, application_id=application_id, content="x")

    with pytest.raises(NotFoundError):
        await service.delete(OTHER_USER, application_id, note.id)
