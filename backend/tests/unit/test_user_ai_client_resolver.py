"""Unit tests for UserAIClientResolver against fakes (no network).

``build_ai_client`` is monkeypatched to a recording stub so these tests assert
*which arguments* the resolver builds a client with, without depending on any
real provider SDK or network call.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

import app.infrastructure.ai.resolver as resolver_module
from app.domain.entities import UserAIKey
from app.domain.value_objects import AIProvider
from app.infrastructure.ai.resolver import UserAIClientResolver
from tests.fakes import FakeCipher, InMemoryUserAIKeyRepository


class _RecordedClient:
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs


def _patch_build_ai_client(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    def _fake_build(**kwargs: Any) -> _RecordedClient:
        calls.append(kwargs)
        return _RecordedClient(**kwargs)

    monkeypatch.setattr(resolver_module, "build_ai_client", _fake_build)
    return calls


def _resolver(repository: InMemoryUserAIKeyRepository) -> UserAIClientResolver:
    return UserAIClientResolver(
        key_repository=repository,
        cipher=FakeCipher(),
        platform_provider="gemini",
        platform_api_key="platform-key",
        platform_model="gemini-2.0-flash",
        platform_max_tokens=4096,
        platform_base_url="",
    )


async def test_resolve_without_saved_key_uses_platform_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _patch_build_ai_client(monkeypatch)
    repository = InMemoryUserAIKeyRepository()
    resolver = _resolver(repository)

    client = await resolver.resolve("user-1")

    assert isinstance(client, _RecordedClient)
    assert calls == [
        {
            "provider": "gemini",
            "api_key": "platform-key",
            "model": "gemini-2.0-flash",
            "max_tokens": 4096,
            "base_url": "",
        }
    ]


async def test_resolve_with_saved_key_uses_users_own_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _patch_build_ai_client(monkeypatch)
    repository = InMemoryUserAIKeyRepository()
    cipher = FakeCipher()
    encrypted_key, nonce = cipher.encrypt("sk-user-own-key", aad="user-1")
    now = datetime.now(UTC)
    await repository.upsert(
        UserAIKey(
            user_id="user-1",
            provider=AIProvider.ANTHROPIC,
            encrypted_key=encrypted_key,
            nonce=nonce,
            key_last4="9key",
            model="claude-3-5-haiku-latest",
            base_url=None,
            created_at=now,
            updated_at=now,
        )
    )
    resolver = _resolver(repository)

    await resolver.resolve("user-1")

    assert calls == [
        {
            "provider": AIProvider.ANTHROPIC,
            "api_key": "sk-user-own-key",
            "model": "claude-3-5-haiku-latest",
            "max_tokens": 4096,
            "base_url": "",
        }
    ]


async def test_two_different_users_get_clients_built_from_their_own_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression guard for the resolver-caching footgun: resolving for one
    user must never leak that user's key into another user's resolved client.
    """
    calls = _patch_build_ai_client(monkeypatch)
    repository = InMemoryUserAIKeyRepository()
    cipher = FakeCipher()
    now = datetime.now(UTC)
    for user_id, secret in (("user-1", "sk-user-1-secret"), ("user-2", "sk-user-2-secret")):
        encrypted_key, nonce = cipher.encrypt(secret, aad=user_id)
        await repository.upsert(
            UserAIKey(
                user_id=user_id,
                provider=AIProvider.OPENAI_COMPATIBLE,
                encrypted_key=encrypted_key,
                nonce=nonce,
                key_last4=secret[-4:],
                model="qwen2.5:14b-instruct",
                base_url="http://localhost:11434/v1",
                created_at=now,
                updated_at=now,
            )
        )
    resolver = _resolver(repository)

    await resolver.resolve("user-1")
    await resolver.resolve("user-2")

    assert [call["api_key"] for call in calls] == [
        "sk-user-1-secret",
        "sk-user-2-secret",
    ]


async def test_resolve_with_no_key_falls_back_after_key_removed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _patch_build_ai_client(monkeypatch)
    repository = InMemoryUserAIKeyRepository()
    cipher = FakeCipher()
    encrypted_key, nonce = cipher.encrypt("sk-user-own-key", aad="user-1")
    now = datetime.now(UTC)
    await repository.upsert(
        UserAIKey(
            user_id="user-1",
            provider=AIProvider.ANTHROPIC,
            encrypted_key=encrypted_key,
            nonce=nonce,
            key_last4="9key",
            model="claude-3-5-haiku-latest",
            base_url=None,
            created_at=now,
            updated_at=now,
        )
    )
    resolver = _resolver(repository)
    await repository.delete("user-1")

    await resolver.resolve("user-1")

    assert calls[-1]["api_key"] == "platform-key"
