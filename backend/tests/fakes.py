"""In-memory fakes implementing the domain interfaces, for fast unit/API tests."""

from __future__ import annotations

import json

from app.domain.ai import AIClient
from app.domain.entities import (
    CV,
    Application,
    ApplicationContact,
    ApplicationNote,
    ApplicationTask,
    TailoredCV,
)
from app.domain.repositories import (
    ApplicationRepository,
    ContactRepository,
    CVRepository,
    NoteRepository,
    TailoredCVRepository,
    TaskRepository,
)


class InMemoryApplicationRepository(ApplicationRepository):
    """Stores applications in a dict. No network, deterministic ordering by insert."""

    def __init__(self) -> None:
        self._store: dict[str, Application] = {}

    async def add(self, application: Application) -> Application:
        self._store[application.id] = application
        return application

    async def list_for_user(self, user_id: str) -> list[Application]:
        items = [a for a in self._store.values() if a.user_id == user_id]
        return sorted(items, key=lambda a: a.created_at, reverse=True)

    async def get(self, user_id: str, application_id: str) -> Application | None:
        application = self._store.get(application_id)
        if application is None or application.user_id != user_id:
            return None
        return application

    async def update(self, application: Application) -> Application:
        self._store[application.id] = application
        return application

    async def delete(self, user_id: str, application_id: str) -> None:
        application = self._store.get(application_id)
        if application is not None and application.user_id == user_id:
            del self._store[application_id]


class InMemoryNoteRepository(NoteRepository):
    """Stores notes in a dict. No network, deterministic ordering by insert."""

    def __init__(self) -> None:
        self._store: dict[str, ApplicationNote] = {}

    async def add(self, note: ApplicationNote) -> ApplicationNote:
        self._store[note.id] = note
        return note

    async def list_for_application(
        self, user_id: str, application_id: str
    ) -> list[ApplicationNote]:
        items = [
            n
            for n in self._store.values()
            if n.user_id == user_id and n.application_id == application_id
        ]
        return sorted(items, key=lambda n: n.created_at, reverse=True)

    async def get(self, user_id: str, note_id: str) -> ApplicationNote | None:
        note = self._store.get(note_id)
        if note is None or note.user_id != user_id:
            return None
        return note

    async def update(self, note: ApplicationNote) -> ApplicationNote:
        self._store[note.id] = note
        return note

    async def delete(self, user_id: str, note_id: str) -> None:
        note = self._store.get(note_id)
        if note is not None and note.user_id == user_id:
            del self._store[note_id]


class InMemoryContactRepository(ContactRepository):
    """Stores contacts in a dict. No network, deterministic ordering by insert."""

    def __init__(self) -> None:
        self._store: dict[str, ApplicationContact] = {}

    async def add(self, contact: ApplicationContact) -> ApplicationContact:
        self._store[contact.id] = contact
        return contact

    async def list_for_application(
        self, user_id: str, application_id: str
    ) -> list[ApplicationContact]:
        return [
            c
            for c in self._store.values()
            if c.user_id == user_id and c.application_id == application_id
        ]

    async def get(self, user_id: str, contact_id: str) -> ApplicationContact | None:
        contact = self._store.get(contact_id)
        if contact is None or contact.user_id != user_id:
            return None
        return contact

    async def update(self, contact: ApplicationContact) -> ApplicationContact:
        self._store[contact.id] = contact
        return contact

    async def delete(self, user_id: str, contact_id: str) -> None:
        contact = self._store.get(contact_id)
        if contact is not None and contact.user_id == user_id:
            del self._store[contact_id]


class InMemoryTaskRepository(TaskRepository):
    """Stores tasks in a dict. No network, deterministic ordering by insert."""

    def __init__(self) -> None:
        self._store: dict[str, ApplicationTask] = {}

    async def add(self, task: ApplicationTask) -> ApplicationTask:
        self._store[task.id] = task
        return task

    async def list_for_application(
        self, user_id: str, application_id: str
    ) -> list[ApplicationTask]:
        return [
            t
            for t in self._store.values()
            if t.user_id == user_id and t.application_id == application_id
        ]

    async def get(self, user_id: str, task_id: str) -> ApplicationTask | None:
        task = self._store.get(task_id)
        if task is None or task.user_id != user_id:
            return None
        return task

    async def update(self, task: ApplicationTask) -> ApplicationTask:
        self._store[task.id] = task
        return task

    async def delete(self, user_id: str, task_id: str) -> None:
        task = self._store.get(task_id)
        if task is not None and task.user_id == user_id:
            del self._store[task_id]


class InMemoryCVRepository(CVRepository):
    """Stores at most one base resume per user_id. No network, no real storage —
    uploaded bytes are recorded for assertions rather than persisted anywhere."""

    def __init__(self) -> None:
        self._store: dict[str, CV] = {}
        self.uploaded_files: dict[str, tuple[bytes, str]] = {}

    async def get_current(self, user_id: str) -> CV | None:
        return self._store.get(user_id)

    async def replace(self, cv: CV, file_bytes: bytes, content_type: str) -> CV:
        await self.delete(cv.user_id)
        self._store[cv.user_id] = cv
        self.uploaded_files[cv.storage_path] = (file_bytes, content_type)
        return cv

    async def delete(self, user_id: str) -> None:
        existing = self._store.pop(user_id, None)
        if existing is not None:
            self.uploaded_files.pop(existing.storage_path, None)


class InMemoryTailoredCVRepository(TailoredCVRepository):
    """Stores tailored CVs in a dict. No network, deterministic ordering by insert."""

    def __init__(self) -> None:
        self._store: dict[str, TailoredCV] = {}

    async def add(self, tailored: TailoredCV) -> TailoredCV:
        self._store[tailored.id] = tailored
        return tailored

    async def get(self, user_id: str, tailored_id: str) -> TailoredCV | None:
        tailored = self._store.get(tailored_id)
        if tailored is None or tailored.user_id != user_id:
            return None
        return tailored

    async def update(self, tailored: TailoredCV) -> TailoredCV:
        self._store[tailored.id] = tailored
        return tailored

    async def list_for_user(self, user_id: str) -> list[TailoredCV]:
        items = [t for t in self._store.values() if t.user_id == user_id]
        return sorted(items, key=lambda t: t.created_at, reverse=True)


# A minimal, valid structured-output JSON payload — the default canned response
# for FakeAIClient, so happy-path tests don't each have to build their own JSON.
DEFAULT_STRUCTURED_AI_RESPONSE = json.dumps(
    {
        "contact": {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": None,
            "location": "Remote",
            "links": [{"label": "GitHub", "url": "https://github.com/janedoe"}],
        },
        "sections": [
            {
                "id": "summary",
                "heading": "Summary",
                "changed": True,
                "body": "Experienced engineer with a track record of shipping.",
                "entries": [],
                "explanation": "Reworded to emphasize experience relevant to the role.",
            },
            {
                "id": "experience",
                "heading": "Professional Experience",
                "changed": False,
                "body": None,
                "entries": [
                    {
                        "title": "Software Engineer",
                        "organization": "Foo Inc",
                        "date_range": "2020 – 2024",
                        "context": None,
                        "bullets": ["Built and shipped Python services."],
                    }
                ],
                "explanation": None,
            },
        ],
    }
)


class FakeAIClient(AIClient):
    """Returns a canned response and records the last call for assertions.

    ``error``, when set, is raised instead — simulating a vendor SDK failure
    (auth, rate limit, network, outage) to exercise the AIGenerationError path
    without depending on any real provider's exception types.
    """

    def __init__(
        self,
        response: str = DEFAULT_STRUCTURED_AI_RESPONSE,
        *,
        error: Exception | None = None,
    ) -> None:
        self._response = response
        self._error = error
        self.last_system: str | None = None
        self.last_prompt: str | None = None

    async def generate(self, *, system: str, prompt: str) -> str:
        self.last_system = system
        self.last_prompt = prompt
        if self._error is not None:
            raise self._error
        return self._response
