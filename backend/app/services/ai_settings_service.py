"""Business logic for a user's BYOK (bring-your-own-key) AI provider setting."""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.crypto import SecretCipher
from app.domain.entities import UserAIKey
from app.domain.repositories import UserAIKeyRepository
from app.domain.value_objects import AIProvider
from app.infrastructure.ai.resolver import build_ai_client

# Keep the save-time validation probe cheap — it only needs to prove the
# key/endpoint is accepted, not produce useful output.
_VALIDATION_SYSTEM_PROMPT = "You are a connectivity check."
_VALIDATION_PROMPT = "Reply with the single word OK."
_VALIDATION_MAX_TOKENS = 16

_KEY_LAST4_LENGTH = 4


class AISettingsService:
    """Use-cases for saving, reading, and removing a user's own AI provider key.

    Depends only on :class:`UserAIKeyRepository` and :class:`SecretCipher`, so it
    runs against the real Supabase repository/AES-GCM cipher in production and
    in-memory fakes in tests.
    """

    def __init__(self, repository: UserAIKeyRepository, cipher: SecretCipher) -> None:
        self._repository = repository
        self._cipher = cipher

    async def get(self, user_id: str) -> UserAIKey | None:
        return await self._repository.get(user_id)

    async def save(
        self,
        *,
        user_id: str,
        provider: AIProvider,
        api_key: str,
        model: str,
        base_url: str | None,
    ) -> UserAIKey:
        # Validate with a real call before persisting anything — a typo caught
        # here is cheap; the same typo caught during a real tailoring request
        # looks exactly like the platform-tier flakiness this feature exists to
        # escape. A rejected probe (bad key, bad model, bad endpoint) raises
        # ProviderAuthenticationError from within build_ai_client's generate();
        # nothing is written on failure.
        probe_client = build_ai_client(
            provider=provider,
            api_key=api_key,
            model=model,
            max_tokens=_VALIDATION_MAX_TOKENS,
            base_url=base_url or "",
        )
        await probe_client.generate(
            system=_VALIDATION_SYSTEM_PROMPT, prompt=_VALIDATION_PROMPT
        )

        encrypted_key, nonce = self._cipher.encrypt(api_key, aad=user_id)
        now = datetime.now(UTC)
        existing = await self._repository.get(user_id)
        key = UserAIKey(
            user_id=user_id,
            provider=provider,
            encrypted_key=encrypted_key,
            nonce=nonce,
            key_last4=api_key[-_KEY_LAST4_LENGTH:],
            model=model,
            base_url=base_url,
            created_at=existing.created_at if existing is not None else now,
            updated_at=now,
        )
        return await self._repository.upsert(key)

    async def delete(self, user_id: str) -> None:
        await self._repository.delete(user_id)
