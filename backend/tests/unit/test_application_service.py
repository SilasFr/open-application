"""Unit tests for ApplicationService against an in-memory repository."""

from __future__ import annotations

import pytest

from app.domain.exceptions import InvalidStatusTransition, NotFoundError
from app.domain.value_objects import ApplicationStatus
from app.services.application_service import ApplicationService
from tests.fakes import InMemoryApplicationRepository

USER = "user-1"


def _service() -> ApplicationService:
    return ApplicationService(InMemoryApplicationRepository())


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
