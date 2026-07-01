"""In-memory fakes implementing the domain interfaces, for fast unit/API tests."""

from __future__ import annotations

from app.domain.ai import AIClient
from app.domain.entities import Application
from app.domain.repositories import ApplicationRepository


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


class FakeAIClient(AIClient):
    """Returns a canned response and records the last call for assertions."""

    def __init__(self, response: str = "# Tailored CV\n\nTailored content.") -> None:
        self._response = response
        self.last_system: str | None = None
        self.last_prompt: str | None = None

    async def generate(self, *, system: str, prompt: str) -> str:
        self.last_system = system
        self.last_prompt = prompt
        return self._response
