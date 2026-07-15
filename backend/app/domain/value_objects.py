"""Value objects for the domain layer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ApplicationStatus(StrEnum):
    """Lifecycle status of a job application."""

    SAVED = "saved"
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    OFFER = "offer"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


# Allowed forward transitions. Terminal states map to an empty set.
_ALLOWED_TRANSITIONS: dict[ApplicationStatus, frozenset[ApplicationStatus]] = {
    ApplicationStatus.SAVED: frozenset(
        {ApplicationStatus.APPLIED, ApplicationStatus.WITHDRAWN}
    ),
    ApplicationStatus.APPLIED: frozenset(
        {
            ApplicationStatus.INTERVIEWING,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        }
    ),
    ApplicationStatus.INTERVIEWING: frozenset(
        {
            ApplicationStatus.OFFER,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        }
    ),
    ApplicationStatus.OFFER: frozenset(
        {
            ApplicationStatus.ACCEPTED,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        }
    ),
    ApplicationStatus.ACCEPTED: frozenset(),
    ApplicationStatus.REJECTED: frozenset(),
    ApplicationStatus.WITHDRAWN: frozenset(),
}


def can_transition(source: ApplicationStatus, target: ApplicationStatus) -> bool:
    """Return True if moving from ``source`` to ``target`` is a legal status change."""

    return target in _ALLOWED_TRANSITIONS[source]


class AIProvider(StrEnum):
    """A supported AI provider a user can bring their own key for."""

    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OPENAI_COMPATIBLE = "openai_compatible"


class NoteType(StrEnum):
    """Kind of entry in an application's activity timeline."""

    NOTE = "note"
    ACTIVITY = "activity"
    EMAIL = "email"
    CALL = "call"
    INTERVIEW = "interview"


@dataclass(frozen=True)
class JobDescription:
    """The text of a job posting a CV can be tailored against."""

    text: str

    def is_empty(self) -> bool:
        return not self.text.strip()
