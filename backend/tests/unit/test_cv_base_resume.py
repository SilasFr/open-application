"""Unit tests for CVService (base-resume upload/replace/remove + validation)."""

from __future__ import annotations

import io

import pytest
from docx import Document

from app.domain.exceptions import NotFoundError, UnsupportedFileError
from app.services.cv_service import CVService
from tests.fakes import InMemoryCVRepository

DOCX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)
PDF_CONTENT_TYPE = "application/pdf"


def _docx_bytes(text: str) -> bytes:
    document = Document()
    document.add_paragraph(text)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


async def test_get_current_raises_not_found_when_none_saved() -> None:
    service = CVService(InMemoryCVRepository())

    with pytest.raises(NotFoundError):
        await service.get_current("user-1")


async def test_upload_extracts_text_and_persists() -> None:
    service = CVService(InMemoryCVRepository())

    cv = await service.upload(
        user_id="user-1",
        filename="resume.docx",
        content_type=DOCX_CONTENT_TYPE,
        file_bytes=_docx_bytes("Jane Doe, Python engineer"),
    )

    assert cv.filename == "resume.docx"
    assert cv.content is not None
    assert "Jane Doe" in cv.content

    fetched = await service.get_current("user-1")
    assert fetched.id == cv.id


async def test_upload_rejects_unsupported_content_type() -> None:
    service = CVService(InMemoryCVRepository())

    with pytest.raises(UnsupportedFileError):
        await service.upload(
            user_id="user-1",
            filename="resume.txt",
            content_type="text/plain",
            file_bytes=b"plain text",
        )


async def test_upload_rejects_oversized_file() -> None:
    service = CVService(InMemoryCVRepository())
    oversized = b"0" * (5 * 1024 * 1024 + 1)

    with pytest.raises(UnsupportedFileError):
        await service.upload(
            user_id="user-1",
            filename="resume.pdf",
            content_type=PDF_CONTENT_TYPE,
            file_bytes=oversized,
        )


async def test_upload_rejects_corrupt_pdf() -> None:
    service = CVService(InMemoryCVRepository())

    with pytest.raises(UnsupportedFileError):
        await service.upload(
            user_id="user-1",
            filename="resume.pdf",
            content_type=PDF_CONTENT_TYPE,
            file_bytes=b"this is not a real pdf",
        )


async def test_replace_keeps_only_one_current_resume() -> None:
    repository = InMemoryCVRepository()
    service = CVService(repository)

    first = await service.upload(
        user_id="user-1",
        filename="v1.docx",
        content_type=DOCX_CONTENT_TYPE,
        file_bytes=_docx_bytes("First version"),
    )
    second = await service.upload(
        user_id="user-1",
        filename="v2.docx",
        content_type=DOCX_CONTENT_TYPE,
        file_bytes=_docx_bytes("Second version"),
    )

    assert first.id != second.id
    current = await service.get_current("user-1")
    assert current.id == second.id
    # The old file's bytes should no longer be tracked.
    assert first.storage_path not in repository.uploaded_files


async def test_delete_removes_current_resume() -> None:
    service = CVService(InMemoryCVRepository())
    await service.upload(
        user_id="user-1",
        filename="resume.docx",
        content_type=DOCX_CONTENT_TYPE,
        file_bytes=_docx_bytes("Jane Doe"),
    )

    await service.delete("user-1")

    with pytest.raises(NotFoundError):
        await service.get_current("user-1")


async def test_delete_is_a_noop_when_nothing_saved() -> None:
    service = CVService(InMemoryCVRepository())
    await service.delete("user-1")  # must not raise
