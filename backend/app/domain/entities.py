"""Domain entities — the core business objects, free of any framework concerns."""

from __future__ import annotations

from dataclasses import dataclass, field
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
    """A base CV uploaded by the user. Exactly one is current per user at a time."""

    id: str
    user_id: str
    filename: str
    storage_path: str
    created_at: datetime
    content: str | None = None


@dataclass
class ContactLink:
    """A labelled URL in the CV header (e.g. LinkedIn, GitHub)."""

    label: str
    url: str


@dataclass
class TailoredCVContact:
    """Header/contact details for a tailored CV, extracted from the base resume."""

    name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    links: list[ContactLink] = field(default_factory=list)


@dataclass
class TailoredCVEntry:
    """A structured item within a section — a role, degree, or similar, with an
    optional right-aligned date range and its own bullet points."""

    title: str
    organization: str | None = None
    date_range: str | None = None
    context: str | None = None
    bullets: list[str] = field(default_factory=list)


@dataclass
class TailoredCVSection:
    """A single section of a structured, AI-tailored CV.

    A section is rendered from either ``body`` (prose sections like Summary or
    Skills) or ``entries`` (structured sections like Experience or Education) —
    at least one is populated, enforced by the service's structured-output
    validation. Sections with ``changed=True`` must carry a non-null
    ``explanation`` (also enforced there, not by this dataclass).
    """

    id: str
    heading: str
    changed: bool
    body: str | None = None
    entries: list[TailoredCVEntry] = field(default_factory=list)
    explanation: str | None = None


@dataclass
class TailoredCV:
    """A CV that has been tailored to a specific job description by the AI."""

    id: str
    user_id: str
    source_cv_id: str | None
    job_description: str
    content: str
    created_at: datetime
    contact: TailoredCVContact | None = None
    sections: list[TailoredCVSection] = field(default_factory=list)
    application_id: str | None = None
    refinement_instructions: str | None = None
    previous_tailored_cv_id: str | None = None
