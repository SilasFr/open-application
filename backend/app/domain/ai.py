"""AI client interface owned by the domain.

All Claude (or any LLM) usage flows through this abstraction. Services depend on
``AIClient``; the concrete Anthropic implementation lives in
``app.infrastructure.ai``. No SDK import happens in this module.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class AIClient(ABC):
    """Contract for text generation used by AI-powered services."""

    @abstractmethod
    async def generate(self, *, system: str, prompt: str) -> str:
        """Return the model's completion for ``prompt`` under ``system`` guidance."""


class AIClientResolver(ABC):
    """Chooses which :class:`AIClient` serves a given user's request.

    Kept separate from ``AIClient`` itself so callers that only need to read
    existing data never pay for a per-user lookup/decrypt — only call sites that
    actually generate text resolve a client, and they do so once per call, per user.
    """

    @abstractmethod
    async def resolve(self, user_id: str) -> AIClient:
        """Return the client to use for ``user_id``: their own configured
        provider/key if set, otherwise the platform's shared client."""
