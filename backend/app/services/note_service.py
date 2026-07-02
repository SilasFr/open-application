"""Business logic for an application's activity timeline and notes."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.domain.entities import ApplicationNote
from app.domain.exceptions import NotFoundError
from app.domain.repositories import ApplicationRepository, NoteRepository
from app.domain.value_objects import NoteType


class NoteService:
    """Use-cases for an application's timeline: notes and (read-only) activity.

    Depends only on the :class:`NoteRepository` and :class:`ApplicationRepository`
    interfaces — the latter is used solely to assert that the caller owns the
    parent application before touching its notes.
    """

    def __init__(
        self,
        repository: NoteRepository,
        application_repository: ApplicationRepository,
    ) -> None:
        self._repository = repository
        self._application_repository = application_repository

    async def _assert_application_owned(self, user_id: str, application_id: str) -> None:
        application = await self._application_repository.get(user_id, application_id)
        if application is None:
            raise NotFoundError(f"Application {application_id} not found")

    async def list(self, user_id: str, application_id: str) -> list[ApplicationNote]:
        await self._assert_application_owned(user_id, application_id)
        return await self._repository.list_for_application(user_id, application_id)

    async def create(
        self,
        *,
        user_id: str,
        application_id: str,
        type: NoteType = NoteType.NOTE,
        content: str,
    ) -> ApplicationNote:
        await self._assert_application_owned(user_id, application_id)
        now = datetime.now(UTC)
        note = ApplicationNote(
            id=str(uuid4()),
            application_id=application_id,
            user_id=user_id,
            type=type,
            content=content,
            created_at=now,
            updated_at=now,
        )
        return await self._repository.add(note)

    async def _get_owned(
        self, user_id: str, application_id: str, note_id: str
    ) -> ApplicationNote:
        await self._assert_application_owned(user_id, application_id)
        note = await self._repository.get(user_id, note_id)
        if note is None or note.application_id != application_id:
            raise NotFoundError(f"Note {note_id} not found")
        return note

    async def update(
        self, user_id: str, application_id: str, note_id: str, content: str
    ) -> ApplicationNote:
        note = await self._get_owned(user_id, application_id, note_id)
        note.content = content
        note.updated_at = datetime.now(UTC)
        return await self._repository.update(note)

    async def delete(self, user_id: str, application_id: str, note_id: str) -> None:
        await self._get_owned(user_id, application_id, note_id)
        await self._repository.delete(user_id, note_id)
