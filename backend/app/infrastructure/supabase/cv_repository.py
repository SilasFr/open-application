"""Supabase implementations of :class:`CVRepository` and :class:`TailoredCVRepository`.

The ``supabase`` Python client is synchronous, so each call is offloaded to a worker
thread via :func:`anyio.to_thread.run_sync` to keep the async event loop unblocked —
same pattern as ``note_repository.py`` and its siblings.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import anyio
from supabase import Client

from app.domain.entities import CV, TailoredCV, TailoredCVSection
from app.domain.repositories import CVRepository, TailoredCVRepository

_CV_BUCKET = "cvs"


def _cv_to_row(cv: CV) -> dict[str, Any]:
    return {
        "id": cv.id,
        "user_id": cv.user_id,
        "filename": cv.filename,
        "storage_path": cv.storage_path,
        "content": cv.content,
        "created_at": cv.created_at.isoformat(),
    }


def _cv_to_entity(row: Any) -> CV:
    return CV(
        id=str(row["id"]),
        user_id=str(row["user_id"]),
        filename=row["filename"],
        storage_path=row["storage_path"],
        created_at=datetime.fromisoformat(row["created_at"]),
        content=row.get("content"),
    )


def _tailored_to_row(tailored: TailoredCV) -> dict[str, Any]:
    return {
        "id": tailored.id,
        "user_id": tailored.user_id,
        "source_cv_id": tailored.source_cv_id,
        "job_description": tailored.job_description,
        "content": tailored.content,
        "sections": [
            {
                "id": section.id,
                "heading": section.heading,
                "body": section.body,
                "changed": section.changed,
                "explanation": section.explanation,
            }
            for section in tailored.sections
        ],
        "application_id": tailored.application_id,
        "refinement_instructions": tailored.refinement_instructions,
        "previous_tailored_cv_id": tailored.previous_tailored_cv_id,
        "created_at": tailored.created_at.isoformat(),
    }


def _tailored_to_entity(row: Any) -> TailoredCV:
    sections = [
        TailoredCVSection(
            id=str(section["id"]),
            heading=section["heading"],
            body=section["body"],
            changed=bool(section["changed"]),
            explanation=section.get("explanation"),
        )
        for section in (row.get("sections") or [])
    ]
    return TailoredCV(
        id=str(row["id"]),
        user_id=str(row["user_id"]),
        source_cv_id=row.get("source_cv_id"),
        job_description=row["job_description"],
        content=row["content"],
        created_at=datetime.fromisoformat(row["created_at"]),
        sections=sections,
        application_id=row.get("application_id"),
        refinement_instructions=row.get("refinement_instructions"),
        previous_tailored_cv_id=row.get("previous_tailored_cv_id"),
    )


class SupabaseCVRepository(CVRepository):
    """Stores the base resume's parsed content in ``cvs`` and the file itself in
    the ``cvs`` Storage bucket, laid out ``<user_id>/<filename>``."""

    _TABLE = "cvs"

    def __init__(self, client: Client) -> None:
        self._client = client

    async def get_current(self, user_id: str) -> CV | None:
        response = await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE)
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = response.data
        return _cv_to_entity(rows[0]) if rows else None

    async def replace(self, cv: CV, file_bytes: bytes, content_type: str) -> CV:
        # Enforce "one current base resume per user" (research.md #3), but never
        # leave the user with *no* resume if a step fails. Order matters:
        # upload + insert the new resume FIRST, and only once it's safely
        # persisted remove the previous row/object. A failure before the insert
        # completes leaves the existing resume fully intact.
        existing = await self.get_current(cv.user_id)

        await anyio.to_thread.run_sync(
            lambda: self._client.storage.from_(_CV_BUCKET).upload(
                cv.storage_path,
                file_bytes,
                {"content-type": content_type, "upsert": "true"},
            )
        )
        row = _cv_to_row(cv)
        response = await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE).insert(row).execute()
        )

        # New resume is now the current one. Best-effort cleanup of the old row
        # and its Storage object. Skip removing the object when the path is
        # unchanged (same filename) — the upsert above already overwrote it.
        if existing is not None:
            await anyio.to_thread.run_sync(
                lambda: self._client.table(self._TABLE)
                .delete()
                .eq("id", existing.id)
                .execute()
            )
            if existing.storage_path != cv.storage_path:
                await anyio.to_thread.run_sync(
                    lambda: self._client.storage.from_(_CV_BUCKET).remove(
                        [existing.storage_path]
                    )
                )
        return _cv_to_entity(response.data[0])

    async def delete(self, user_id: str) -> None:
        existing = await self.get_current(user_id)
        if existing is None:
            return
        await anyio.to_thread.run_sync(
            lambda: self._client.storage.from_(_CV_BUCKET).remove(
                [existing.storage_path]
            )
        )
        await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE)
            .delete()
            .eq("user_id", user_id)
            .execute()
        )


class SupabaseTailoredCVRepository(TailoredCVRepository):
    """Stores tailored CVs (including their structured ``sections``) in
    ``tailored_cvs``."""

    _TABLE = "tailored_cvs"

    def __init__(self, client: Client) -> None:
        self._client = client

    async def add(self, tailored: TailoredCV) -> TailoredCV:
        row = _tailored_to_row(tailored)
        response = await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE).insert(row).execute()
        )
        return _tailored_to_entity(response.data[0])

    async def get(self, user_id: str, tailored_id: str) -> TailoredCV | None:
        response = await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE)
            .select("*")
            .eq("user_id", user_id)
            .eq("id", tailored_id)
            .limit(1)
            .execute()
        )
        rows = response.data
        return _tailored_to_entity(rows[0]) if rows else None

    async def update(self, tailored: TailoredCV) -> TailoredCV:
        row = _tailored_to_row(tailored)
        response = await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE)
            .update(row)
            .eq("user_id", tailored.user_id)
            .eq("id", tailored.id)
            .execute()
        )
        return _tailored_to_entity(response.data[0])

    async def list_for_user(self, user_id: str) -> list[TailoredCV]:
        response = await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE)
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return [_tailored_to_entity(row) for row in response.data]
