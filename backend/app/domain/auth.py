"""Authentication interface owned by the domain.

The API layer identifies callers through :class:`TokenVerifier`; the concrete
Supabase implementation lives in ``app.infrastructure.auth``. No JWT library or
vendor SDK is imported here.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class AuthenticatedUser:
    """The identity extracted from a verified access token."""

    id: str
    email: str | None = None


class TokenVerifier(ABC):
    """Contract for verifying a bearer access token and identifying the user."""

    @abstractmethod
    def verify(self, token: str) -> AuthenticatedUser:
        """Return the authenticated user, or raise ``AuthenticationError``."""
