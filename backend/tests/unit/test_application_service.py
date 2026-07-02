"""Unit tests for ApplicationService against an in-memory repository."""

from __future__ import annotations

import pytest

from app.domain.exceptions import InvalidStatusTransition, NotFoundError
from app.domain.value_objects import ApplicationStatus, NoteType
from app.services.application_service import ApplicationService
from tests.fakes import InMemoryApplicationRepository, InMemoryNoteRepository

USER = "user-1"


def _service(
    note_repository: InMemoryNoteRepository | None = None,
) -> ApplicationService:
    return ApplicationService(
        InMemoryApplicationRepository(), note_repository or InMemoryNoteRepository()
    )


async def test_create_defaults_to_saved_and_is_listed() -> None:
    service = _service()

    created = await service.create(user_id=USER, company="Acme", role="Engineer")

    assert created.status is ApplicationStatus.SAVED
    assert created.company == "Acme"
    listed = await service.list(USER)
    assert [a.id for a in listed] == [created.id]


async def test_list_is_scoped_to_owner() -> None:
    service = _service()
    await service.create(user_id=USER, company="Acme", role="Engineer")

    assert await service.list("someone-else") == []


async def test_get_missing_raises_not_found() -> None:
    service = _service()

    with pytest.raises(NotFoundError):
        await service.get(USER, "does-not-exist")


async def test_valid_status_transition() -> None:
    service = _service()
    created = await service.create(user_id=USER, company="Acme", role="Engineer")

    updated = await service.change_status(USER, created.id, ApplicationStatus.APPLIED)

    assert updated.status is ApplicationStatus.APPLIED
    assert updated.updated_at >= created.updated_at


async def test_invalid_status_transition_raises() -> None:
    service = _service()
    created = await service.create(user_id=USER, company="Acme", role="Engineer")

    # SAVED -> OFFER is not a legal transition.
    with pytest.raises(InvalidStatusTransition):
        await service.change_status(USER, created.id, ApplicationStatus.OFFER)


async def test_delete_then_get_raises() -> None:
    service = _service()
    created = await service.create(user_id=USER, company="Acme", role="Engineer")

    await service.delete(USER, created.id)

    with pytest.raises(NotFoundError):
        await service.get(USER, created.id)


async def test_status_change_records_timeline_activity() -> None:
    notes = InMemoryNoteRepository()
    service = _service(notes)
    created = await service.create(user_id=USER, company="Acme", role="Engineer")

    await service.change_status(USER, created.id, ApplicationStatus.APPLIED)

    timeline = await notes.list_for_application(USER, created.id)
    assert len(timeline) == 1
    assert timeline[0].type is NoteType.ACTIVITY
    assert timeline[0].content == "Moved to Applied"


async def test_invalid_status_transition_records_no_activity() -> None:
    notes = InMemoryNoteRepository()
    service = _service(notes)
    created = await service.create(user_id=USER, company="Acme", role="Engineer")

    with pytest.raises(InvalidStatusTransition):
        await service.change_status(USER, created.id, ApplicationStatus.OFFER)

    assert await notes.list_for_application(USER, created.id) == []
