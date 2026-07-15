"""Unit tests for AISettingsService against fakes (no network).

``build_ai_client`` is monkeypatched to a stub factory so these tests exercise
the service's validate-then-persist logic without depending on any real
provider SDK or network call.
"""

from __future__ import annotations

import pytest

import app.services.ai_settings_service as ai_settings_service
from app.domain.ai import AIClient
from app.domain.exceptions import ProviderAuthenticationError
from app.domain.value_objects import AIProvider
from app.services.ai_settings_service import AISettingsService
from tests.fakes import FakeCipher, InMemoryUserAIKeyRepository


class _StubProbeClient(AIClient):
    def __init__(self, *, error: Exception | None = None) -> None:
        self._error = error

    async def generate(self, *, system: str, prompt: str) -> str:
        if self._error is not None:
            raise self._error
        return "OK"


def _patch_build_ai_client(monkeypatch: pytest.MonkeyPatch, client: AIClient) -> None:
    monkeypatch.setattr(
        ai_settings_service, "build_ai_client", lambda **kwargs: client
    )


def _make_service() -> tuple[AISettingsService, InMemoryUserAIKeyRepository]:
    repository = InMemoryUserAIKeyRepository()
    service = AISettingsService(repository, FakeCipher())
    return service, repository


async def test_save_validates_key_before_storing(monkeypatch: pytest.MonkeyPatch) -> None:
    service, repository = _make_service()
    _patch_build_ai_client(monkeypatch, _StubProbeClient())

    saved = await service.save(
        user_id="user-1",
        provider=AIProvider.ANTHROPIC,
        api_key="sk-ant-abcd1234",
        model="claude-3-5-haiku-latest",
        base_url=None,
    )

    assert saved.provider == AIProvider.ANTHROPIC
    assert saved.key_last4 == "1234"
    assert saved.encrypted_key != "sk-ant-abcd1234"
    stored = await repository.get("user-1")
    assert stored is not None
    assert stored.model == "claude-3-5-haiku-latest"


async def test_save_never_returns_or_stores_plaintext_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, repository = _make_service()
    _patch_build_ai_client(monkeypatch, _StubProbeClient())

    saved = await service.save(
        user_id="user-1",
        provider=AIProvider.GEMINI,
        api_key="AIzaSy-super-secret-0000",
        model="gemini-2.0-flash",
        base_url=None,
    )

    stored = await repository.get("user-1")
    assert stored is not None
    assert "AIzaSy-super-secret-0000" not in stored.encrypted_key
    assert "AIzaSy-super-secret-0000" not in repr(saved)


async def test_rejected_probe_raises_and_stores_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, repository = _make_service()
    _patch_build_ai_client(
        monkeypatch, _StubProbeClient(error=ProviderAuthenticationError("rejected"))
    )

    with pytest.raises(ProviderAuthenticationError):
        await service.save(
            user_id="user-1",
            provider=AIProvider.ANTHROPIC,
            api_key="sk-ant-invalid",
            model="claude-3-5-haiku-latest",
            base_url=None,
        )

    assert await repository.get("user-1") is None


async def test_delete_reverts_to_free_tier(monkeypatch: pytest.MonkeyPatch) -> None:
    service, repository = _make_service()
    _patch_build_ai_client(monkeypatch, _StubProbeClient())
    await service.save(
        user_id="user-1",
        provider=AIProvider.ANTHROPIC,
        api_key="sk-ant-abcd1234",
        model="claude-3-5-haiku-latest",
        base_url=None,
    )

    await service.delete("user-1")

    assert await service.get("user-1") is None


async def test_save_preserves_created_at_across_updates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, repository = _make_service()
    _patch_build_ai_client(monkeypatch, _StubProbeClient())
    first = await service.save(
        user_id="user-1",
        provider=AIProvider.ANTHROPIC,
        api_key="sk-ant-abcd1234",
        model="claude-3-5-haiku-latest",
        base_url=None,
    )

    second = await service.save(
        user_id="user-1",
        provider=AIProvider.GEMINI,
        api_key="AIzaSy-newkey0000",
        model="gemini-2.0-flash",
        base_url=None,
    )

    assert second.created_at == first.created_at
    assert second.provider == AIProvider.GEMINI


async def test_get_returns_none_when_unset() -> None:
    service, _ = _make_service()

    assert await service.get("user-1") is None
