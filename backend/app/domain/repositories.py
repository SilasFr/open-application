"""Repository interfaces owned by the domain.

Services depend on these abstractions; concrete implementations live in
``app.infrastructure``. This is the dependency-inversion boundary that keeps the
business logic free of Supabase (or any other vendor).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities import Application


class ApplicationRepository(ABC):
    """Persistence contract for :class:`~app.domain.entities.Application`."""

    @abstractmethod
    async def add(self, application: Application) -> Application:
        """Persist a new application and return the stored entity."""

    @abstractmethod
    async def list_for_user(self, user_id: str) -> list[Application]:
        """Return all applications owned by ``user_id`` (newest first)."""

    @abstractmethod
    async def get(self, user_id: str, application_id: str) -> Application | None:
        """Return the owned application, or ``None`` if it does not exist."""

    @abstractmethod
    async def update(self, application: Application) -> Application:
        """Persist changes to an existing application and return it."""

    @abstractmethod
    async def delete(self, user_id: str, application_id: str) -> None:
        """Remove an owned application. No-op if it does not exist."""
