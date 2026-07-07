"""Render a tailored CV's structured sections as downloadable PDF/DOCX documents.

Renders directly from the structured ``sections`` list (heading + body) rather
than converting from an intermediate HTML/DOCX form (research.md #2). Both
libraries are pure-Python with no system dependencies.
"""

from __future__ import annotations

import io

from docx import Document
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.domain.entities import TailoredCVSection

PDF_CONTENT_TYPE = "application/pdf"
DOCX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)


def render_pdf(sections: list[TailoredCVSection]) -> bytes:
    """Render ``sections`` as a simple, ATS-friendly PDF document."""

    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        spaceBefore=12,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "SectionBody",
        parent=styles["BodyText"],
        spaceAfter=6,
        leading=14,
    )

    flowables = []
    for section in sections:
        flowables.append(Paragraph(_escape(section.heading), heading_style))
        for line in section.body.splitlines() or [""]:
            flowables.append(Paragraph(_escape(line) or "&nbsp;", body_style))
        flowables.append(Spacer(1, 6))

    document.build(flowables)
    return buffer.getvalue()


def render_docx(sections: list[TailoredCVSection]) -> bytes:
    """Render ``sections`` as a simple DOCX document."""

    document = Document()
    for section in sections:
        document.add_heading(section.heading, level=2)
        for line in section.body.splitlines() or [""]:
            document.add_paragraph(line)

    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def _escape(text: str) -> str:
    """Escape the handful of characters reportlab's mini-markup treats specially."""

    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
