"""Unit tests for TaskService against in-memory repositories."""

from __future__ import annotations

import pytest

from app.domain.exceptions import NotFoundError
from app.services.application_service import ApplicationService
from app.services.task_service import TaskService
from tests.fakes import (
    InMemoryApplicationRepository,
    InMemoryNoteRepository,
    InMemoryTaskRepository,
)

USER = "user-1"
OTHER_USER = "user-2"


async def _setup() -> tuple[TaskService, str]:
    """Return a TaskService plus an application id owned by USER."""
    applications = InMemoryApplicationRepository()
    app_service = ApplicationService(applications, InMemoryNoteRepository())
    application = await app_service.create(user_id=USER, company="Acme", role="Engineer")
    return TaskService(InMemoryTaskRepository(), applications), application.id


async def test_create_starts_unchecked_and_is_listed() -> None:
    service, application_id = await _setup()

    task = await service.create(
        user_id=USER, application_id=application_id, title="Send thank-you email"
    )

    assert task.is_completed is False
    listed = await service.list(USER, application_id)
    assert [t.id for t in listed] == [task.id]


async def test_create_rejects_unowned_application() -> None:
    service, application_id = await _setup()

    with pytest.raises(NotFoundError):
        await service.create(user_id=OTHER_USER, application_id=application_id, title="x")


async def test_toggle_completion() -> None:
    service, application_id = await _setup()
    task = await service.create(
        user_id=USER, application_id=application_id, title="Tailor CV"
    )

    updated = await service.update(
        USER, application_id, task.id, is_completed=True
    )

    assert updated.is_completed is True
    assert updated.title == "Tailor CV"


async def test_update_missing_task_raises() -> None:
    service, application_id = await _setup()

    with pytest.raises(NotFoundError):
        await service.update(USER, application_id, "does-not-exist", is_completed=True)


async def test_delete_then_list_empty() -> None:
    service, application_id = await _setup()
    task = await service.create(user_id=USER, application_id=application_id, title="x")

    await service.delete(USER, application_id, task.id)

    assert await service.list(USER, application_id) == []


async def test_delete_rejects_unowned_application() -> None:
    service, application_id = await _setup()
    task = await service.create(user_id=USER, application_id=application_id, title="x")

    with pytest.raises(NotFoundError):
        await service.delete(OTHER_USER, application_id, task.id)
