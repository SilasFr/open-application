"""Business logic for a user's single, persisted base resume."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.domain.entities import CV
from app.domain.exceptions import NotFoundError, UnsupportedFileError
from app.domain.repositories import CVRepository
from app.infrastructure.cv_text_extraction import (
    MAX_FILE_SIZE_BYTES,
    SUPPORTED_CONTENT_TYPES,
    extract_text,
)


class CVService:
    """Use-cases for uploading, replacing, fetching, and removing a base resume.

    Depends only on the :class:`CVRepository` interface, so it runs against the
    real Supabase repository in production and an in-memory fake in tests.
    """

    def __init__(self, repository: CVRepository) -> None:
        self._repository = repository

    async def get_current(self, user_id: str) -> CV:
        cv = await self._repository.get_current(user_id)
        if cv is None:
            raise NotFoundError("No base resume saved for this user")
        return cv

    async def upload(
        self,
        *,
        user_id: str,
        filename: str,
        content_type: str,
        file_bytes: bytes,
    ) -> CV:
        if content_type not in SUPPORTED_CONTENT_TYPES:
            raise UnsupportedFileError(
                "Unsupported file type — please upload a PDF or DOCX file."
            )
        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise UnsupportedFileError("File exceeds the 5 MB size limit.")

        content = extract_text(
            filename=filename, content_type=content_type, file_bytes=file_bytes
        )
        cv = CV(
            id=str(uuid4()),
            user_id=user_id,
            filename=filename,
            storage_path=f"{user_id}/{filename}",
            created_at=datetime.now(UTC),
            content=content,
        )
        return await self._repository.replace(cv, file_bytes, content_type)

    async def delete(self, user_id: str) -> None:
        await self._repository.delete(user_id)
