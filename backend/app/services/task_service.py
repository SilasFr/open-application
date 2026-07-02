"""Business logic for an application's task checklist."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.domain.entities import ApplicationTask
from app.domain.exceptions import NotFoundError
from app.domain.repositories import ApplicationRepository, TaskRepository


class TaskService:
    """Use-cases for an application's checklist tasks.

    Depends only on the :class:`TaskRepository` and :class:`ApplicationRepository`
    interfaces — the latter is used solely to assert that the caller owns the
    parent application before touching its tasks.
    """

    def __init__(
        self,
        repository: TaskRepository,
        application_repository: ApplicationRepository,
    ) -> None:
        self._repository = repository
        self._application_repository = application_repository

    async def _assert_application_owned(self, user_id: str, application_id: str) -> None:
        application = await self._application_repository.get(user_id, application_id)
        if application is None:
            raise NotFoundError(f"Application {application_id} not found")

    async def list(self, user_id: str, application_id: str) -> list[ApplicationTask]:
        await self._assert_application_owned(user_id, application_id)
        return await self._repository.list_for_application(user_id, application_id)

    async def create(
        self,
        *,
        user_id: str,
        application_id: str,
        title: str,
        due_date: datetime | None = None,
    ) -> ApplicationTask:
        await self._assert_application_owned(user_id, application_id)
        task = ApplicationTask(
            id=str(uuid4()),
            application_id=application_id,
            user_id=user_id,
            title=title,
            is_completed=False,
            due_date=due_date,
            created_at=datetime.now(UTC),
        )
        return await self._repository.add(task)

    async def _get_owned(
        self, user_id: str, application_id: str, task_id: str
    ) -> ApplicationTask:
        await self._assert_application_owned(user_id, application_id)
        task = await self._repository.get(user_id, task_id)
        if task is None or task.application_id != application_id:
            raise NotFoundError(f"Task {task_id} not found")
        return task

    async def update(
        self,
        user_id: str,
        application_id: str,
        task_id: str,
        *,
        title: str | None = None,
        is_completed: bool | None = None,
        due_date: datetime | None = None,
    ) -> ApplicationTask:
        task = await self._get_owned(user_id, application_id, task_id)
        if title is not None:
            task.title = title
        if is_completed is not None:
            task.is_completed = is_completed
        if due_date is not None:
            task.due_date = due_date
        return await self._repository.update(task)

    async def delete(self, user_id: str, application_id: str, task_id: str) -> None:
        await self._get_owned(user_id, application_id, task_id)
        await self._repository.delete(user_id, task_id)
