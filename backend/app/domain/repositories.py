"""Repository interfaces owned by the domain.

Services depend on these abstractions; concrete implementations live in
``app.infrastructure``. This is the dependency-inversion boundary that keeps the
business logic free of Supabase (or any other vendor).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities import (
    CV,
    Application,
    ApplicationContact,
    ApplicationNote,
    ApplicationTask,
    TailoredCV,
)


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


class NoteRepository(ABC):
    """Persistence contract for :class:`~app.domain.entities.ApplicationNote`."""

    @abstractmethod
    async def add(self, note: ApplicationNote) -> ApplicationNote:
        """Persist a new note/activity entry and return the stored entity."""

    @abstractmethod
    async def list_for_application(
        self, user_id: str, application_id: str
    ) -> list[ApplicationNote]:
        """Return the owned application's timeline, newest first."""

    @abstractmethod
    async def get(
        self, user_id: str, note_id: str
    ) -> ApplicationNote | None:
        """Return the owned note, or ``None`` if it does not exist."""

    @abstractmethod
    async def update(self, note: ApplicationNote) -> ApplicationNote:
        """Persist changes to an existing note and return it."""

    @abstractmethod
    async def delete(self, user_id: str, note_id: str) -> None:
        """Remove an owned note. No-op if it does not exist."""


class ContactRepository(ABC):
    """Persistence contract for :class:`~app.domain.entities.ApplicationContact`."""

    @abstractmethod
    async def add(self, contact: ApplicationContact) -> ApplicationContact:
        """Persist a new contact and return the stored entity."""

    @abstractmethod
    async def list_for_application(
        self, user_id: str, application_id: str
    ) -> list[ApplicationContact]:
        """Return the owned application's contacts."""

    @abstractmethod
    async def get(
        self, user_id: str, contact_id: str
    ) -> ApplicationContact | None:
        """Return the owned contact, or ``None`` if it does not exist."""

    @abstractmethod
    async def update(self, contact: ApplicationContact) -> ApplicationContact:
        """Persist changes to an existing contact and return it."""

    @abstractmethod
    async def delete(self, user_id: str, contact_id: str) -> None:
        """Remove an owned contact. No-op if it does not exist."""


class TaskRepository(ABC):
    """Persistence contract for :class:`~app.domain.entities.ApplicationTask`."""

    @abstractmethod
    async def add(self, task: ApplicationTask) -> ApplicationTask:
        """Persist a new task and return the stored entity."""

    @abstractmethod
    async def list_for_application(
        self, user_id: str, application_id: str
    ) -> list[ApplicationTask]:
        """Return the owned application's checklist, in creation order."""

    @abstractmethod
    async def get(self, user_id: str, task_id: str) -> ApplicationTask | None:
        """Return the owned task, or ``None`` if it does not exist."""

    @abstractmethod
    async def update(self, task: ApplicationTask) -> ApplicationTask:
        """Persist changes to an existing task and return it."""

    @abstractmethod
    async def delete(self, user_id: str, task_id: str) -> None:
        """Remove an owned task. No-op if it does not exist."""


class CVRepository(ABC):
    """Persistence contract for a user's single, current base resume.

    Only one :class:`~app.domain.entities.CV` row exists per ``user_id`` at a
    time (research.md #3) — enforced here via delete-then-insert semantics on
    ``replace``, not by a schema flag.
    """

    @abstractmethod
    async def get_current(self, user_id: str) -> CV | None:
        """Return the user's current base resume, or ``None`` if none is saved."""

    @abstractmethod
    async def replace(self, cv: CV, file_bytes: bytes, content_type: str) -> CV:
        """Delete any existing base resume (row + Storage object) for
        ``cv.user_id``, store ``file_bytes`` at ``cv.storage_path``, insert
        ``cv``, and return the stored entity."""

    @abstractmethod
    async def delete(self, user_id: str) -> None:
        """Remove the user's current base resume (row + Storage object). No-op
        if none exists."""


class TailoredCVRepository(ABC):
    """Persistence contract for :class:`~app.domain.entities.TailoredCV`."""

    @abstractmethod
    async def add(self, tailored: TailoredCV) -> TailoredCV:
        """Persist a newly generated tailored CV and return the stored entity."""

    @abstractmethod
    async def get(self, user_id: str, tailored_id: str) -> TailoredCV | None:
        """Return the owned tailored CV, or ``None`` if it does not exist."""

    @abstractmethod
    async def update(self, tailored: TailoredCV) -> TailoredCV:
        """Persist changes to an existing tailored CV (e.g. attaching it to an
        application) and return it."""

    @abstractmethod
    async def list_for_user(self, user_id: str) -> list[TailoredCV]:
        """Return all tailored CVs owned by ``user_id`` (newest first)."""
