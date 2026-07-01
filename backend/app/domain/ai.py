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
