"""Gemini-backed implementation of the :class:`AIClient` interface.

Free-tier alternative to Anthropic — see https://ai.google.dev for API key setup.
"""

from __future__ import annotations

from google import genai
from google.genai import errors, types

from app.domain.ai import AIClient
from app.domain.exceptions import ProviderAuthenticationError

_AUTH_STATUS_CODES = {401, 403}


class GeminiClient(AIClient):
    """Generates text with Gemini via the official ``google-genai`` async SDK."""

    def __init__(self, *, api_key: str, model: str, max_tokens: int) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    async def generate(self, *, system: str, prompt: str) -> str:
        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    max_output_tokens=self._max_tokens,
                ),
            )
        except errors.ClientError as exc:
            if exc.code in _AUTH_STATUS_CODES:
                # Actionable by the user (fix your key) — see
                # ProviderAuthenticationError.
                raise ProviderAuthenticationError(
                    "The Gemini API key was rejected."
                ) from exc
            raise
        return response.text or ""
