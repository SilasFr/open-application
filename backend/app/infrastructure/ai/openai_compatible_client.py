"""``AIClient`` backed by any OpenAI-compatible ``/chat/completions`` endpoint.

One implementation covers a whole family of servers that speak the OpenAI wire
format: a local **Ollama** or **llama.cpp** server on Apple Silicon for
development, and hosted open-model APIs (Groq, Together, DeepInfra, OpenRouter,
vLLM) in production. Only the ``base_url`` (and, for hosted providers, the
``api_key``) changes between them.

No vendor SDK — a thin ``httpx`` call, matching the repositories' style and
keeping the dependency surface minimal (Constitution Principle III/V).
"""

from __future__ import annotations

from typing import Any

import httpx

from app.domain.ai import AIClient
from app.domain.exceptions import ProviderAuthenticationError

_AUTH_STATUS_CODES = {401, 403}

# LLM generation — especially a local model's first (cold) call — is slow
# relative to a normal HTTP request. Give it real headroom rather than the
# httpx 5s default, which would spuriously fail long completions.
_REQUEST_TIMEOUT_SECONDS = 120.0


class OpenAICompatibleClient(AIClient):
    """Generates text via a POST to ``{base_url}/chat/completions``.

    ``base_url`` must include the API version segment the server expects, e.g.
    ``http://localhost:11434/v1`` for Ollama. ``api_key`` is sent as a bearer
    token when set and omitted when empty (local Ollama ignores it).
    """

    def __init__(
        self, *, base_url: str, api_key: str, model: str, max_tokens: int
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._max_tokens = max_tokens

    async def generate(self, *, system: str, prompt: str) -> str:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload: dict[str, Any] = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            # JSON mode: the CV-tailoring caller parses the response with a strict
            # ``json.loads``, so force the server to emit a single JSON object and
            # avoid the markdown-fence/preamble failure mode of free-form output.
            "response_format": {"type": "json_object"},
        }

        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            if response.status_code in _AUTH_STATUS_CODES:
                # Actionable by the user (fix your key) — see
                # ProviderAuthenticationError. Checked before the generic >=400
                # branch so a BYOK auth failure isn't swallowed into the same
                # bucket as rate limits/outages.
                raise ProviderAuthenticationError(
                    "The provider API key was rejected."
                )
            if response.status_code >= 400:
                # Surface the provider's error body (rate-limit details, model
                # errors, auth) — httpx's default HTTPStatusError message drops
                # it, which makes 429s/400s undiagnosable from logs alone.
                raise RuntimeError(
                    f"AI provider returned HTTP {response.status_code}: "
                    f"{response.text[:500]}"
                )
            data = response.json()

        # Let a malformed response raise (KeyError/IndexError/TypeError); the
        # tailoring service's broad handler maps any failure here to a clean,
        # retryable AIGenerationError rather than an unhandled 500.
        content = data["choices"][0]["message"]["content"]
        return content if isinstance(content, str) else ""
