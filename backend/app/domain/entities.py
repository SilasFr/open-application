"""Domain entities — the core business objects, free of any framework concerns."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.value_objects import ApplicationStatus, NoteType


@dataclass
class Application:
    """A single job application the user is tracking."""

    id: str
    user_id: str
    company: str
    role: str
    status: ApplicationStatus
    job_description: str | None
    created_at: datetime
    updated_at: datetime


@dataclass
class ApplicationNote:
    """A timeline entry for an application: a user note or an auto-generated activity."""

    id: str
    application_id: str
    user_id: str
    type: NoteType
    content: str
    created_at: datetime
    updated_at: datetime


@dataclass
class ApplicationContact:
    """A professional contact (recruiter, hiring manager, referrer) related to an application."""

    id: str
    application_id: str
    user_id: str
    name: str
    role: str | None
    email: str | None
    phone: str | None
    linkedin_url: str | None
    notes: str | None
    created_at: datetime


@dataclass
class ApplicationTask:
    """A checklist item for an application (e.g. "Send thank-you email")."""

    id: str
    application_id: str
    user_id: str
    title: str
    is_completed: bool
    due_date: datetime | None
    created_at: datetime


@dataclass
class CV:
    """A base CV uploaded by the user."""

    id: str
    user_id: str
    filename: str
    storage_path: str
    content: str | None = None


@dataclass
class TailoredCV:
    """A CV that has been tailored to a specific job description by the AI."""

    id: str
    user_id: str
    source_cv_id: str | None
    job_description: str
    content: str
    created_at: datetime
