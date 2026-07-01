"""Unit tests for SupabaseTokenVerifier using the HS256 (shared-secret) path."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pytest

from app.domain.exceptions import AuthenticationError
from app.infrastructure.auth.supabase_verifier import SupabaseTokenVerifier

SECRET = "super-secret-test-key-at-least-32-bytes-long"
ISSUER = "https://ref.supabase.co/auth/v1"
AUDIENCE = "authenticated"


def _make_token(secret: str = SECRET, **overrides: Any) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "email": "jane@example.com",
        "aud": AUDIENCE,
        "iss": ISSUER,
        "iat": now,
        "exp": now + timedelta(hours=1),
    }
    payload.update(overrides)
    return jwt.encode(payload, secret, algorithm="HS256")


def _verifier() -> SupabaseTokenVerifier:
    return SupabaseTokenVerifier(jwt_secret=SECRET, issuer=ISSUER, audience=AUDIENCE)


def test_valid_token_returns_user() -> None:
    user = _verifier().verify(_make_token())
    assert user.id == "11111111-1111-1111-1111-111111111111"
    assert user.email == "jane@example.com"


def test_expired_token_rejected() -> None:
    expired = _make_token(exp=datetime.now(UTC) - timedelta(minutes=1))
    with pytest.raises(AuthenticationError):
        _verifier().verify(expired)


def test_wrong_audience_rejected() -> None:
    with pytest.raises(AuthenticationError):
        _verifier().verify(_make_token(aud="anon"))


def test_wrong_issuer_rejected() -> None:
    with pytest.raises(AuthenticationError):
        _verifier().verify(_make_token(iss="https://evil.example.com/auth/v1"))


def test_bad_signature_rejected() -> None:
    with pytest.raises(AuthenticationError):
        _verifier().verify(
            _make_token(secret="a-different-secret-also-at-least-32-bytes-x")
        )


def test_missing_subject_rejected() -> None:
    # A token with no sub claim must be rejected (require: exp, sub).
    with pytest.raises(AuthenticationError):
        _verifier().verify(_make_token(sub=None))


def test_garbage_token_rejected() -> None:
    with pytest.raises(AuthenticationError):
        _verifier().verify("not-a-jwt")
