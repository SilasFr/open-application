"""Domain-level exceptions. The API layer maps these to HTTP responses."""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain/business-rule violations.

    ``code`` is a stable, machine-readable identifier included in the JSON error
    body so clients can branch on the failure *kind* without string-matching the
    human-readable message (which is free to change/localize). Subclasses set
    their own code; the message is passed at raise time as usual.
    """

    code: str = "domain_error"


class AuthenticationError(DomainError):
    """The caller could not be authenticated (missing/invalid/expired token)."""

    code = "authentication_error"


class NotFoundError(DomainError):
    """A requested entity does not exist (or is not owned by the caller)."""

    code = "not_found"


class BaseResumeNotFoundError(NotFoundError):
    """The user has no saved base resume. A distinct code lets the frontend
    route the user back to the upload step instead of showing a generic error."""

    code = "base_resume_not_found"


class InvalidStatusTransition(DomainError):
    """An application status change is not permitted by the lifecycle rules."""

    code = "invalid_status_transition"


class UnsupportedFileError(DomainError):
    """An uploaded file is the wrong type, too large, or could not be parsed."""

    code = "unsupported_file"


class InvalidAIResponseError(DomainError):
    """The AI client returned a response that failed structured-output validation."""

    code = "invalid_ai_response"


class AIGenerationError(DomainError):
    """The configured AI provider failed outright (auth, rate limit, network,
    outage, etc.) while generating a response. Deliberately provider-agnostic —
    the service layer must not know or care which vendor raised the underlying
    error (Constitution Principle III/V: AI is abstracted behind AIClient)."""

    code = "ai_generation_error"
