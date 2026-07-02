"""Business logic for the application tracker."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.domain.entities import Application, ApplicationNote
from app.domain.exceptions import InvalidStatusTransition, NotFoundError
from app.domain.repositories import ApplicationRepository, NoteRepository
from app.domain.value_objects import ApplicationStatus, NoteType, can_transition


class ApplicationService:
    """Use-cases for creating and progressing job applications.

    Depends only on the :class:`ApplicationRepository` and :class:`NoteRepository`
    interfaces, so it can run against real Supabase repositories in production and
    in-memory fakes in tests.
    """

    def __init__(
        self, repository: ApplicationRepository, note_repository: NoteRepository
    ) -> None:
        self._repository = repository
        self._note_repository = note_repository

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
        updated = await self._repository.update(application)
        await self._record_status_change_activity(updated)
        return updated

    async def _record_status_change_activity(self, application: Application) -> None:
        now = datetime.now(UTC)
        note = ApplicationNote(
            id=str(uuid4()),
            application_id=application.id,
            user_id=application.user_id,
            type=NoteType.ACTIVITY,
            content=f"Moved to {application.status.value.capitalize()}",
            created_at=now,
            updated_at=now,
        )
        await self._note_repository.add(note)

    async def delete(self, user_id: str, application_id: str) -> None:
        # Ensures the application exists and is owned by the caller before deleting.
        await self.get(user_id, application_id)
        await self._repository.delete(user_id, application_id)
