"""Ordering guarantees for SupabaseCVRepository.replace().

The real Supabase repo must never leave a user with *no* base resume if a step
of a replace fails — the new resume is persisted before the old one is removed.
These tests drive the repo against a minimal fake Supabase client so the
ordering is asserted without a live backend.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from app.domain.entities import CV
from app.infrastructure.supabase.cv_repository import SupabaseCVRepository


class _FakeQuery:
    def __init__(self, table: _FakeTable, op: str) -> None:
        self._table = table
        self._op = op
        self._filters: dict[str, Any] = {}

    def select(self, *_: Any) -> _FakeQuery:
        return self

    def insert(self, row: dict[str, Any]) -> _FakeQuery:
        self._row = row
        return self

    def delete(self) -> _FakeQuery:
        self._op = "delete"
        return self

    def eq(self, column: str, value: Any) -> _FakeQuery:
        self._filters[column] = value
        return self

    def order(self, *_: Any, **__: Any) -> _FakeQuery:
        return self

    def limit(self, *_: Any) -> _FakeQuery:
        return self

    def execute(self) -> Any:
        if self._op == "select":
            rows = [r for r in self._table.rows if _matches(r, self._filters)]
            rows.sort(key=lambda r: r["created_at"], reverse=True)
            return type("Resp", (), {"data": rows[:1]})
        if self._op == "insert":
            if self._table.fail_insert:
                raise RuntimeError("insert boom")
            self._table.rows.append(self._row)
            return type("Resp", (), {"data": [self._row]})
        if self._op == "delete":
            self._table.rows = [
                r for r in self._table.rows if not _matches(r, self._filters)
            ]
            return type("Resp", (), {"data": []})
        raise AssertionError(self._op)


def _matches(row: dict[str, Any], filters: dict[str, Any]) -> bool:
    return all(row.get(k) == v for k, v in filters.items())


class _FakeTable:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []
        self.fail_insert = False

    def select(self, *a: Any) -> _FakeQuery:
        return _FakeQuery(self, "select").select(*a)

    def insert(self, row: dict[str, Any]) -> _FakeQuery:
        return _FakeQuery(self, "insert").insert(row)

    def delete(self) -> _FakeQuery:
        return _FakeQuery(self, "delete").delete()


class _FakeBucket:
    def __init__(self) -> None:
        self.objects: set[str] = set()

    def upload(self, path: str, _bytes: bytes, _opts: dict[str, Any]) -> None:
        self.objects.add(path)

    def remove(self, paths: list[str]) -> None:
        self.objects.difference_update(paths)


class _FakeStorage:
    def __init__(self, bucket: _FakeBucket) -> None:
        self._bucket = bucket

    def from_(self, _name: str) -> _FakeBucket:
        return self._bucket


class _FakeClient:
    def __init__(self) -> None:
        self._table = _FakeTable()
        self.bucket = _FakeBucket()
        self._storage = _FakeStorage(self.bucket)

    def table(self, _name: str) -> _FakeTable:
        return self._table

    @property
    def storage(self) -> _FakeStorage:
        return self._storage


def _cv(user_id: str, filename: str) -> CV:
    return CV(
        id=f"id-{filename}",
        user_id=user_id,
        filename=filename,
        storage_path=f"{user_id}/{filename}",
        created_at=datetime.now(UTC),
        content="parsed text",
    )


async def test_replace_removes_previous_after_persisting_new() -> None:
    client = _FakeClient()
    repo = SupabaseCVRepository(client)  # type: ignore[arg-type]

    await repo.replace(_cv("user-1", "old.pdf"), b"old", "application/pdf")
    await repo.replace(_cv("user-1", "new.pdf"), b"new", "application/pdf")

    current = await repo.get_current("user-1")
    assert current is not None
    assert current.filename == "new.pdf"
    # Exactly one row remains, and the stale object was cleaned up.
    assert len(client.table("cvs").rows) == 1
    assert client.bucket.objects == {"user-1/new.pdf"}


async def test_replace_leaves_existing_intact_when_insert_fails() -> None:
    client = _FakeClient()
    repo = SupabaseCVRepository(client)  # type: ignore[arg-type]

    await repo.replace(_cv("user-1", "old.pdf"), b"old", "application/pdf")

    client.table("cvs").fail_insert = True  # type: ignore[attr-defined]
    with pytest.raises(RuntimeError):
        await repo.replace(_cv("user-1", "new.pdf"), b"new", "application/pdf")

    # The previous resume must still be retrievable — no data loss.
    current = await repo.get_current("user-1")
    assert current is not None
    assert current.filename == "old.pdf"
    assert "user-1/old.pdf" in client.bucket.objects
