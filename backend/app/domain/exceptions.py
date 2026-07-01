"""Domain-level exceptions. The API layer maps these to HTTP responses."""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain/business-rule violations."""


class NotFoundError(DomainError):
    """A requested entity does not exist (or is not owned by the caller)."""


class InvalidStatusTransition(DomainError):
    """An application status change is not permitted by the lifecycle rules."""
