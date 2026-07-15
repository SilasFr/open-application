"""Request/response models for the BYOK AI settings API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.entities import UserAIKey
from app.domain.value_objects import AIProvider


class AISettingsRead(BaseModel):
    """A saved BYOK configuration. Never carries the plaintext key or the
    ciphertext — only enough to display and confirm what's saved."""

    provider: AIProvider
    model: str
    base_url: str | None
    key_last4: str
    created_at: datetime

    @classmethod
    def from_entity(cls, key: UserAIKey) -> AISettingsRead:
        return cls(
            provider=key.provider,
            model=key.model,
            base_url=key.base_url,
            key_last4=key.key_last4,
            created_at=key.created_at,
        )


class SaveAISettingsRequest(BaseModel):
    provider: AIProvider
    api_key: str = Field(min_length=1)
    model: str = Field(min_length=1)
    base_url: str | None = Field(default=None, min_length=1)
