"""Domain-level exceptions. The API layer maps these to HTTP responses."""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain/business-rule violations."""


class AuthenticationError(DomainError):
    """The caller could not be authenticated (missing/invalid/expired token)."""


class NotFoundError(DomainError):
    """A requested entity does not exist (or is not owned by the caller)."""


class InvalidStatusTransition(DomainError):
    """An application status change is not permitted by the lifecycle rules."""


class UnsupportedFileError(DomainError):
    """An uploaded file is the wrong type, too large, or could not be parsed."""


class InvalidAIResponseError(DomainError):
    """The AI client returned a response that failed structured-output validation."""


class AIGenerationError(DomainError):
    """The configured AI provider failed outright (auth, rate limit, network,
    outage, etc.) while generating a response. Deliberately provider-agnostic —
    the service layer must not know or care which vendor raised the underlying
    error (Constitution Principle III/V: AI is abstracted behind AIClient)."""
