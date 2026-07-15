"""Builds :class:`AIClient` instances and resolves which one serves a user.

``build_ai_client`` is the single place the provider name maps to a concrete
class — both the platform's shared client and a user's BYOK client go through
it, so there is exactly one if/elif to keep in sync when a provider is added.
"""

from __future__ import annotations

from app.domain.ai import AIClient, AIClientResolver
from app.domain.crypto import SecretCipher
from app.domain.repositories import UserAIKeyRepository
from app.domain.value_objects import AIProvider
from app.infrastructure.ai.anthropic_client import AnthropicClient
from app.infrastructure.ai.gemini_client import GeminiClient
from app.infrastructure.ai.openai_compatible_client import OpenAICompatibleClient


def build_ai_client(
    *,
    provider: str,
    api_key: str,
    model: str,
    max_tokens: int,
    base_url: str = "",
) -> AIClient:
    """Construct the concrete :class:`AIClient` for ``provider``."""

    if provider == AIProvider.ANTHROPIC:
        return AnthropicClient(api_key=api_key, model=model, max_tokens=max_tokens)
    if provider == AIProvider.OPENAI_COMPATIBLE:
        return OpenAICompatibleClient(
            base_url=base_url, api_key=api_key, model=model, max_tokens=max_tokens
        )
    return GeminiClient(api_key=api_key, model=model, max_tokens=max_tokens)


class UserAIClientResolver(AIClientResolver):
    """Resolves a user's own BYOK client if configured, else the platform's
    shared (env-configured) client.

    Built fresh per request from a per-request dependency chain — see the
    ``get_ai_client_resolver`` provider in ``core/dependencies.py``. This class
    and its provider MUST NOT be cached: caching a resolved client would
    cross-wire one user's key into another user's request.
    """

    def __init__(
        self,
        *,
        key_repository: UserAIKeyRepository,
        cipher: SecretCipher,
        platform_provider: str,
        platform_api_key: str,
        platform_model: str,
        platform_max_tokens: int,
        platform_base_url: str = "",
    ) -> None:
        self._key_repository = key_repository
        self._cipher = cipher
        self._platform_provider = platform_provider
        self._platform_api_key = platform_api_key
        self._platform_model = platform_model
        self._platform_max_tokens = platform_max_tokens
        self._platform_base_url = platform_base_url

    async def resolve(self, user_id: str) -> AIClient:
        saved = await self._key_repository.get(user_id)
        if saved is None:
            return build_ai_client(
                provider=self._platform_provider,
                api_key=self._platform_api_key,
                model=self._platform_model,
                max_tokens=self._platform_max_tokens,
                base_url=self._platform_base_url,
            )

        api_key = self._cipher.decrypt(saved.encrypted_key, saved.nonce, aad=user_id)
        return build_ai_client(
            provider=saved.provider,
            api_key=api_key,
            model=saved.model,
            max_tokens=self._platform_max_tokens,
            base_url=saved.base_url or "",
        )
