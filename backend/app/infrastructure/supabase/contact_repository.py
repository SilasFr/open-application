"""Supabase implementation of :class:`ContactRepository`.

The ``supabase`` Python client is synchronous, so each call is offloaded to a worker
thread via :func:`anyio.to_thread.run_sync` to keep the async event loop unblocked.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import anyio
from supabase import Client

from app.domain.entities import ApplicationContact
from app.domain.repositories import ContactRepository


def _to_row(contact: ApplicationContact) -> dict[str, Any]:
    return {
        "id": contact.id,
        "application_id": contact.application_id,
        "user_id": contact.user_id,
        "name": contact.name,
        "role": contact.role,
        "email": contact.email,
        "phone": contact.phone,
        "linkedin_url": contact.linkedin_url,
        "notes": contact.notes,
        "created_at": contact.created_at.isoformat(),
    }


def _to_entity(row: Any) -> ApplicationContact:
    # ``row`` is a JSON object returned by the Supabase client (loosely typed).
    return ApplicationContact(
        id=str(row["id"]),
        application_id=str(row["application_id"]),
        user_id=str(row["user_id"]),
        name=row["name"],
        role=row.get("role"),
        email=row.get("email"),
        phone=row.get("phone"),
        linkedin_url=row.get("linkedin_url"),
        notes=row.get("notes"),
        created_at=datetime.fromisoformat(row["created_at"]),
    )


class SupabaseContactRepository(ContactRepository):
    """Stores contacts in the Supabase ``application_contacts`` table."""

    _TABLE = "application_contacts"

    def __init__(self, client: Client) -> None:
        self._client = client

    async def add(self, contact: ApplicationContact) -> ApplicationContact:
        row = _to_row(contact)
        response = await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE).insert(row).execute()
        )
        return _to_entity(response.data[0])

    async def list_for_application(
        self, user_id: str, application_id: str
    ) -> list[ApplicationContact]:
        response = await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE)
            .select("*")
            .eq("user_id", user_id)
            .eq("application_id", application_id)
            .order("created_at")
            .execute()
        )
        return [_to_entity(row) for row in response.data]

    async def get(self, user_id: str, contact_id: str) -> ApplicationContact | None:
        response = await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE)
            .select("*")
            .eq("user_id", user_id)
            .eq("id", contact_id)
            .limit(1)
            .execute()
        )
        rows = response.data
        return _to_entity(rows[0]) if rows else None

    async def update(self, contact: ApplicationContact) -> ApplicationContact:
        row = _to_row(contact)
        response = await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE)
            .update(row)
            .eq("user_id", contact.user_id)
            .eq("id", contact.id)
            .execute()
        )
        return _to_entity(response.data[0])

    async def delete(self, user_id: str, contact_id: str) -> None:
        await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE)
            .delete()
            .eq("user_id", user_id)
            .eq("id", contact_id)
            .execute()
        )
