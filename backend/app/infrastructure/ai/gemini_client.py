"""Gemini-backed implementation of the :class:`AIClient` interface.

Free-tier alternative to Anthropic — see https://ai.google.dev for API key setup.
"""

from __future__ import annotations

from google import genai
from google.genai import types

from app.domain.ai import AIClient


class GeminiClient(AIClient):
    """Generates text with Gemini via the official ``google-genai`` async SDK."""

    def __init__(self, *, api_key: str, model: str, max_tokens: int) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    async def generate(self, *, system: str, prompt: str) -> str:
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=self._max_tokens,
            ),
        )
        return response.text or ""
