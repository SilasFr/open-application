"""Unit tests for OpenAICompatibleClient — no network (httpx.MockTransport)."""

from __future__ import annotations

import json

import httpx
import pytest

from app.infrastructure.ai.openai_compatible_client import OpenAICompatibleClient

# Captured before any monkeypatch so the factory below builds a real client
# (with the injected mock transport) instead of recursing into the patch.
_REAL_ASYNC_CLIENT = httpx.AsyncClient


async def test_generate_posts_expected_request_and_returns_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("Authorization")
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": '{"sections": []}'}}]},
        )

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(
        httpx, "AsyncClient", _async_client_factory(transport)
    )

    client = OpenAICompatibleClient(
        base_url="http://localhost:11434/v1/",  # trailing slash trimmed
        api_key="secret-key",
        model="qwen2.5:7b-instruct",
        max_tokens=1024,
    )
    result = await client.generate(system="SYS", prompt="USER")

    assert result == '{"sections": []}'
    assert captured["url"] == "http://localhost:11434/v1/chat/completions"
    assert captured["auth"] == "Bearer secret-key"
    body = captured["body"]
    assert isinstance(body, dict)
    assert body["model"] == "qwen2.5:7b-instruct"
    assert body["max_tokens"] == 1024
    assert body["response_format"] == {"type": "json_object"}
    assert body["messages"] == [
        {"role": "system", "content": "SYS"},
        {"role": "user", "content": "USER"},
    ]


async def test_generate_omits_auth_header_when_no_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("Authorization")
        return httpx.Response(
            200, json={"choices": [{"message": {"content": "ok"}}]}
        )

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(httpx, "AsyncClient", _async_client_factory(transport))

    client = OpenAICompatibleClient(
        base_url="http://localhost:11434/v1",
        api_key="",
        model="m",
        max_tokens=10,
    )
    await client.generate(system="s", prompt="p")

    assert seen["auth"] is None


async def test_generate_raises_on_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "boom"})

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(httpx, "AsyncClient", _async_client_factory(transport))

    client = OpenAICompatibleClient(
        base_url="http://localhost:11434/v1", api_key="", model="m", max_tokens=10
    )
    # Surfaced to the caller (the tailoring service maps it to AIGenerationError).
    with pytest.raises(httpx.HTTPStatusError):
        await client.generate(system="s", prompt="p")


def _async_client_factory(transport: httpx.MockTransport):
    """Return an httpx.AsyncClient factory pinned to ``transport``.

    The production client constructs ``httpx.AsyncClient(timeout=...)``; this
    wrapper injects the mock transport while preserving that call signature.
    """

    def factory(*args: object, **kwargs: object) -> httpx.AsyncClient:
        kwargs.pop("transport", None)
        return _REAL_ASYNC_CLIENT(*args, transport=transport, **kwargs)  # type: ignore[arg-type]

    return factory
