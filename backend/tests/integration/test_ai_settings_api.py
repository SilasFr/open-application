"""API-level tests for the BYOK AI settings routes.

Builds its own app instance (rather than using the shared ``client`` fixture)
so each test controls the ``AISettingsService``'s repository directly for
assertions, and ``build_ai_client`` is monkeypatched to a stub so the
save-time validation probe never touches the network.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.services.ai_settings_service as ai_settings_service
from app.core.dependencies import get_ai_settings_service
from app.core.security import get_current_user_id
from app.domain.ai import AIClient
from app.domain.exceptions import ProviderAuthenticationError
from app.main import create_app
from app.services.ai_settings_service import AISettingsService
from tests.fakes import FakeCipher, InMemoryUserAIKeyRepository

_TEST_USER_ID = "user-api"
HEADERS = {"Authorization": "Bearer irrelevant-real-auth-is-overridden"}


class _StubProbeClient(AIClient):
    def __init__(self, *, error: Exception | None = None) -> None:
        self._error = error

    async def generate(self, *, system: str, prompt: str) -> str:
        if self._error is not None:
            raise self._error
        return "OK"


@pytest.fixture
def repository() -> InMemoryUserAIKeyRepository:
    return InMemoryUserAIKeyRepository()


@pytest.fixture
def client(
    repository: InMemoryUserAIKeyRepository, monkeypatch: pytest.MonkeyPatch
) -> Iterator[TestClient]:
    monkeypatch.setattr(
        ai_settings_service,
        "build_ai_client",
        lambda **kwargs: _StubProbeClient(),
    )
    app = create_app()
    app.dependency_overrides[get_current_user_id] = lambda: _TEST_USER_ID
    app.dependency_overrides[get_ai_settings_service] = lambda: AISettingsService(
        repository, FakeCipher()
    )
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def unauthed_client(repository: InMemoryUserAIKeyRepository) -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_ai_settings_service] = lambda: AISettingsService(
        repository, FakeCipher()
    )
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _save_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "provider": "anthropic",
        "api_key": "sk-ant-abcd1234",
        "model": "claude-3-5-haiku-latest",
    }
    payload.update(overrides)
    return payload


def test_get_settings_unauthed_returns_401(unauthed_client: TestClient) -> None:
    response = unauthed_client.get("/api/v1/settings/ai")
    assert response.status_code == 401


def test_get_settings_when_unset_returns_null(client: TestClient) -> None:
    response = client.get("/api/v1/settings/ai", headers=HEADERS)
    assert response.status_code == 200
    assert response.json() is None


def test_put_then_get_round_trips(client: TestClient) -> None:
    put_response = client.put(
        "/api/v1/settings/ai", json=_save_payload(), headers=HEADERS
    )
    assert put_response.status_code == 200
    body = put_response.json()
    assert body["provider"] == "anthropic"
    assert body["model"] == "claude-3-5-haiku-latest"
    assert body["key_last4"] == "1234"

    get_response = client.get("/api/v1/settings/ai", headers=HEADERS)
    assert get_response.status_code == 200
    assert get_response.json()["key_last4"] == "1234"


def test_response_never_contains_plaintext_key_or_ciphertext(
    client: TestClient, repository: InMemoryUserAIKeyRepository
) -> None:
    response = client.put(
        "/api/v1/settings/ai", json=_save_payload(), headers=HEADERS
    )
    body_text = response.text
    assert "sk-ant-abcd1234" not in body_text

    stored = repository._store["user-api"]  # noqa: SLF001 — test-only introspection
    assert stored.encrypted_key not in body_text


def test_invalid_key_is_rejected_and_nothing_is_stored(
    client: TestClient,
    repository: InMemoryUserAIKeyRepository,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ai_settings_service,
        "build_ai_client",
        lambda **kwargs: _StubProbeClient(
            error=ProviderAuthenticationError("The Anthropic API key was rejected.")
        ),
    )

    response = client.put(
        "/api/v1/settings/ai",
        json=_save_payload(api_key="sk-ant-invalid"),
        headers=HEADERS,
    )

    assert response.status_code == 400
    assert response.json()["code"] == "provider_auth_error"
    assert repository._store == {}  # noqa: SLF001 — test-only introspection


def test_delete_reverts_to_free_tier(client: TestClient) -> None:
    client.put("/api/v1/settings/ai", json=_save_payload(), headers=HEADERS)

    delete_response = client.delete("/api/v1/settings/ai", headers=HEADERS)
    assert delete_response.status_code == 204

    get_response = client.get("/api/v1/settings/ai", headers=HEADERS)
    assert get_response.json() is None
