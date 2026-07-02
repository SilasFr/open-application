"""Supabase implementation of :class:`TaskRepository`.

The ``supabase`` Python client is synchronous, so each call is offloaded to a worker
thread via :func:`anyio.to_thread.run_sync` to keep the async event loop unblocked.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import anyio
from supabase import Client

from app.domain.entities import ApplicationTask
from app.domain.repositories import TaskRepository


def _to_row(task: ApplicationTask) -> dict[str, Any]:
    return {
        "id": task.id,
        "application_id": task.application_id,
        "user_id": task.user_id,
        "title": task.title,
        "is_completed": task.is_completed,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "created_at": task.created_at.isoformat(),
    }


def _to_entity(row: Any) -> ApplicationTask:
    # ``row`` is a JSON object returned by the Supabase client (loosely typed).
    due_date = row.get("due_date")
    return ApplicationTask(
        id=str(row["id"]),
        application_id=str(row["application_id"]),
        user_id=str(row["user_id"]),
        title=row["title"],
        is_completed=bool(row["is_completed"]),
        due_date=datetime.fromisoformat(due_date) if due_date else None,
        created_at=datetime.fromisoformat(row["created_at"]),
    )


class SupabaseTaskRepository(TaskRepository):
    """Stores tasks in the Supabase ``application_tasks`` table."""

    _TABLE = "application_tasks"

    def __init__(self, client: Client) -> None:
        self._client = client

    async def add(self, task: ApplicationTask) -> ApplicationTask:
        row = _to_row(task)
        response = await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE).insert(row).execute()
        )
        return _to_entity(response.data[0])

    async def list_for_application(
        self, user_id: str, application_id: str
    ) -> list[ApplicationTask]:
        response = await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE)
            .select("*")
            .eq("user_id", user_id)
            .eq("application_id", application_id)
            .order("created_at")
            .execute()
        )
        return [_to_entity(row) for row in response.data]

    async def get(self, user_id: str, task_id: str) -> ApplicationTask | None:
        response = await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE)
            .select("*")
            .eq("user_id", user_id)
            .eq("id", task_id)
            .limit(1)
            .execute()
        )
        rows = response.data
        return _to_entity(rows[0]) if rows else None

    async def update(self, task: ApplicationTask) -> ApplicationTask:
        row = _to_row(task)
        response = await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE)
            .update(row)
            .eq("user_id", task.user_id)
            .eq("id", task.id)
            .execute()
        )
        return _to_entity(response.data[0])

    async def delete(self, user_id: str, task_id: str) -> None:
        await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE)
            .delete()
            .eq("user_id", user_id)
            .eq("id", task_id)
            .execute()
        )
