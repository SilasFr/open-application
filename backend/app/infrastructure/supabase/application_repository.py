"""Supabase implementation of :class:`ApplicationRepository`.

The ``supabase`` Python client is synchronous, so each call is offloaded to a worker
thread via :func:`anyio.to_thread.run_sync` to keep the async event loop unblocked.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import anyio
from supabase import Client

from app.domain.entities import Application
from app.domain.repositories import ApplicationRepository
from app.domain.value_objects import ApplicationStatus


def _to_row(application: Application) -> dict[str, Any]:
    return {
        "id": application.id,
        "user_id": application.user_id,
        "company": application.company,
        "role": application.role,
        "status": application.status.value,
        "job_description": application.job_description,
        "created_at": application.created_at.isoformat(),
        "updated_at": application.updated_at.isoformat(),
    }


def _to_entity(row: Any) -> Application:
    # ``row`` is a JSON object returned by the Supabase client (loosely typed).
    return Application(
        id=str(row["id"]),
        user_id=str(row["user_id"]),
        company=row["company"],
        role=row["role"],
        status=ApplicationStatus(row["status"]),
        job_description=row.get("job_description"),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


class SupabaseApplicationRepository(ApplicationRepository):
    """Stores applications in the Supabase ``applications`` table."""

    _TABLE = "applications"

    def __init__(self, client: Client) -> None:
        self._client = client

    async def add(self, application: Application) -> Application:
        row = _to_row(application)
        response = await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE).insert(row).execute()
        )
        return _to_entity(response.data[0])

    async def list_for_user(self, user_id: str) -> list[Application]:
        response = await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE)
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return [_to_entity(row) for row in response.data]

    async def get(self, user_id: str, application_id: str) -> Application | None:
        response = await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE)
            .select("*")
            .eq("user_id", user_id)
            .eq("id", application_id)
            .limit(1)
            .execute()
        )
        rows = response.data
        return _to_entity(rows[0]) if rows else None

    async def update(self, application: Application) -> Application:
        row = _to_row(application)
        response = await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE)
            .update(row)
            .eq("user_id", application.user_id)
            .eq("id", application.id)
            .execute()
        )
        return _to_entity(response.data[0])

    async def delete(self, user_id: str, application_id: str) -> None:
        await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE)
            .delete()
            .eq("user_id", user_id)
            .eq("id", application_id)
            .execute()
        )
