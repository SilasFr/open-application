"""Plain-text extraction from uploaded base-resume files (PDF/DOCX).

Pure-Python, no system dependencies (research.md #1). Extracted text only needs
to feed an LLM prompt, so exact visual fidelity is not a goal — just faithful
text content.
"""

from __future__ import annotations

import io

from docx import Document
from pypdf import PdfReader

from app.domain.exceptions import UnsupportedFileError

PDF_CONTENT_TYPE = "application/pdf"
DOCX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)

SUPPORTED_CONTENT_TYPES = frozenset({PDF_CONTENT_TYPE, DOCX_CONTENT_TYPE})

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB, per FR-013.


def extract_text(*, filename: str, content_type: str, file_bytes: bytes) -> str:
    """Extract plain text from a PDF or DOCX file's raw bytes.

    Raises ``UnsupportedFileError`` if ``content_type`` isn't one of
    ``SUPPORTED_CONTENT_TYPES`` or the file cannot be parsed (corrupt/malformed).
    """

    if content_type == PDF_CONTENT_TYPE:
        return _extract_pdf(file_bytes)
    if content_type == DOCX_CONTENT_TYPE:
        return _extract_docx(file_bytes)
    raise UnsupportedFileError(
        f"Unsupported file type for '{filename}': {content_type}. "
        "Please upload a PDF or DOCX file."
    )


def _extract_pdf(file_bytes: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:  # pypdf raises varied exception types on corrupt PDFs
        raise UnsupportedFileError("Could not read the PDF file — it may be corrupt.") from exc
    return "\n".join(pages).strip()


def _extract_docx(file_bytes: bytes) -> str:
    try:
        document = Document(io.BytesIO(file_bytes))
        paragraphs = [paragraph.text for paragraph in document.paragraphs]
    except Exception as exc:  # python-docx raises varied exception types on corrupt files
        raise UnsupportedFileError("Could not read the DOCX file — it may be corrupt.") from exc
    return "\n".join(paragraphs).strip()
