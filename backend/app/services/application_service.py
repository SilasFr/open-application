"""Business logic for the application tracker."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.domain.entities import Application
from app.domain.exceptions import InvalidStatusTransition, NotFoundError
from app.domain.repositories import ApplicationRepository
from app.domain.value_objects import ApplicationStatus, can_transition


class ApplicationService:
    """Use-cases for creating and progressing job applications.

    Depends only on the :class:`ApplicationRepository` interface, so it can run
    against a real Supabase repository in production and an in-memory fake in tests.
    """

    def __init__(self, repository: ApplicationRepository) -> None:
        self._repository = repository

    async def create(
        self,
        *,
        user_id: str,
        company: str,
        role: str,
        job_description: str | None = None,
    ) -> Application:
        now = datetime.now(UTC)
        application = Application(
            id=str(uuid4()),
            user_id=user_id,
            company=company,
            role=role,
            status=ApplicationStatus.SAVED,
            job_description=job_description,
            created_at=now,
            updated_at=now,
        )
        return await self._repository.add(application)

    async def list(self, user_id: str) -> list[Application]:
        return await self._repository.list_for_user(user_id)

    async def get(self, user_id: str, application_id: str) -> Application:
        application = await self._repository.get(user_id, application_id)
        if application is None:
            raise NotFoundError(f"Application {application_id} not found")
        return application

    async def change_status(
        self, user_id: str, application_id: str, new_status: ApplicationStatus
    ) -> Application:
        application = await self.get(user_id, application_id)
        if not can_transition(application.status, new_status):
            raise InvalidStatusTransition(
                f"Cannot move application from {application.status.value} "
                f"to {new_status.value}"
            )
        application.status = new_status
        application.updated_at = datetime.now(UTC)
        return await self._repository.update(application)

    async def delete(self, user_id: str, application_id: str) -> None:
        # Ensures the application exists and is owned by the caller before deleting.
        await self.get(user_id, application_id)
        await self._repository.delete(user_id, application_id)
