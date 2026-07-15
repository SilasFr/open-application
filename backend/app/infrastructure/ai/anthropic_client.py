"""Anthropic-backed implementation of the :class:`AIClient` interface."""

from __future__ import annotations

import anthropic
from anthropic import AsyncAnthropic

from app.domain.ai import AIClient
from app.domain.exceptions import ProviderAuthenticationError


class AnthropicClient(AIClient):
    """Generates text with Claude via the official ``anthropic`` async SDK.

    The model id and token budget are injected as configuration — never hardcoded —
    per the project constitution.
    """

    def __init__(self, *, api_key: str, model: str, max_tokens: int) -> None:
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    async def generate(self, *, system: str, prompt: str) -> str:
        try:
            message = await self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as exc:
            # Distinct from any other failure: a rejected/revoked key is
            # actionable by the user (fix your key), not a platform outage —
            # see ProviderAuthenticationError.
            raise ProviderAuthenticationError(
                "The Anthropic API key was rejected."
            ) from exc
        return "".join(
            block.text for block in message.content if block.type == "text"
        )
