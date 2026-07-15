"""Supabase implementation of :class:`UserAIKeyRepository`."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import anyio
from supabase import Client

from app.domain.entities import UserAIKey
from app.domain.repositories import UserAIKeyRepository
from app.domain.value_objects import AIProvider


def _to_row(key: UserAIKey) -> dict[str, Any]:
    return {
        "user_id": key.user_id,
        "provider": key.provider.value,
        "encrypted_key": key.encrypted_key,
        "nonce": key.nonce,
        "key_last4": key.key_last4,
        "model": key.model,
        "base_url": key.base_url,
        "created_at": key.created_at.isoformat(),
        "updated_at": key.updated_at.isoformat(),
    }


def _to_entity(row: Any) -> UserAIKey:
    return UserAIKey(
        user_id=str(row["user_id"]),
        provider=AIProvider(row["provider"]),
        encrypted_key=row["encrypted_key"],
        nonce=row["nonce"],
        key_last4=row["key_last4"],
        model=row["model"],
        base_url=row.get("base_url"),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


class SupabaseUserAIKeyRepository(UserAIKeyRepository):
    """Stores each user's single BYOK configuration in ``user_ai_keys``."""

    _TABLE = "user_ai_keys"

    def __init__(self, client: Client) -> None:
        self._client = client

    async def get(self, user_id: str) -> UserAIKey | None:
        response = await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE)
            .select("*")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        rows = response.data
        return _to_entity(rows[0]) if rows else None

    async def upsert(self, key: UserAIKey) -> UserAIKey:
        row = _to_row(key)
        response = await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE)
            .upsert(row, on_conflict="user_id")
            .execute()
        )
        return _to_entity(response.data[0])

    async def delete(self, user_id: str) -> None:
        await anyio.to_thread.run_sync(
            lambda: self._client.table(self._TABLE)
            .delete()
            .eq("user_id", user_id)
            .execute()
        )
