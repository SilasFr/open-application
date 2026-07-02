"""Supabase implementation of :class:`NoteRepository`.

The ``supabase`` Python client is synchronous, so each call is offloaded to a worker
thread via :func:`anyio.to_thread.run_sync` to keep the async event loop unblocked.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import anyio
from supabase import Client

from app.domain.entities import ApplicationNote
from app.domain.repositories import NoteRepository
from app.domain.value_objects import NoteType


def _to_row(note: ApplicationNote) -> dict[str, Any]:
    return {
        "id": note.id,
        "application_id": note.application_id,
        "user_id": note.user_id,
        "type": note.type.value,
        "content": note.content,
        "created_at": note.created_at.isoformat(),
        "updated_at": note.updated_at.isoformat(),
    }


def _to_entity(row: Any) -> ApplicationNote:
    # ``row`` is a JSON object returned by the Supabase client (loosely typed).
    return ApplicationNote(
        id=str(row["id"]),
        application_id=str(row["application_id"]),
        user_id=str(row["user_id"]),
        type=NoteType(row["type"]),
        content=row["content"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


class SupabaseNoteRepository(NoteRepository):
    """Stores notes in the Supabase ``application_notes`` table."""

    _TABLE = "application_notes"

    def __init__(self, client: Client) -> None:
        self._client = client

    async def add(self, note: ApplicationNote) -> ApplicationNote:
        row = _to_row(note)
        response = await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE).insert(row).execute()
        )
        return _to_entity(response.data[0])

    async def list_for_application(
        self, user_id: str, application_id: str
    ) -> list[ApplicationNote]:
        response = await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE)
            .select("*")
            .eq("user_id", user_id)
            .eq("application_id", application_id)
            .order("created_at", desc=True)
            .execute()
        )
        return [_to_entity(row) for row in response.data]

    async def get(self, user_id: str, note_id: str) -> ApplicationNote | None:
        response = await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE)
            .select("*")
            .eq("user_id", user_id)
            .eq("id", note_id)
            .limit(1)
            .execute()
        )
        rows = response.data
        return _to_entity(rows[0]) if rows else None

    async def update(self, note: ApplicationNote) -> ApplicationNote:
        row = _to_row(note)
        response = await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE)
            .update(row)
            .eq("user_id", note.user_id)
            .eq("id", note.id)
            .execute()
        )
        return _to_entity(response.data[0])

    async def delete(self, user_id: str, note_id: str) -> None:
        await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE)
            .delete()
            .eq("user_id", user_id)
            .eq("id", note_id)
            .execute()
        )
