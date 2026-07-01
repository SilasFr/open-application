"""Supabase implementation of :class:`TokenVerifier`.

Verifies a Supabase access token (a JWT) locally, with no per-request network
call in the common case. Supports both signing systems Supabase offers:

* **Asymmetric signing keys (default for new projects)** — RS256/ES256 verified
  against the project's JWKS endpoint. Keys are fetched once and cached.
* **Legacy HS256 shared secret** — verified with ``SUPABASE_JWT_SECRET``.

The issuer and audience are validated when configured (Supabase issues tokens
with issuer ``<url>/auth/v1`` and audience ``authenticated``).
"""

from __future__ import annotations

from typing import Any

import jwt
from jwt import PyJWKClient

from app.domain.auth import AuthenticatedUser, TokenVerifier
from app.domain.exceptions import AuthenticationError

_ASYMMETRIC_ALGORITHMS = ["RS256", "ES256"]
_REQUIRED_CLAIMS = ["exp", "sub"]


class SupabaseTokenVerifier(TokenVerifier):
    def __init__(
        self,
        *,
        jwt_secret: str = "",
        jwks_url: str = "",
        issuer: str = "",
        audience: str = "authenticated",
    ) -> None:
        self._secret = jwt_secret
        self._issuer = issuer
        self._audience = audience
        # Prefer the shared secret when provided (legacy); otherwise use JWKS.
        self._jwks_client = (
            PyJWKClient(jwks_url) if jwks_url and not jwt_secret else None
        )

    def verify(self, token: str) -> AuthenticatedUser:
        payload = self._decode(token)
        subject = payload.get("sub")
        if not subject:
            raise AuthenticationError("Token is missing a subject (sub) claim")
        return AuthenticatedUser(id=str(subject), email=payload.get("email"))

    def _decode(self, token: str) -> dict[str, Any]:
        issuer = self._issuer or None
        try:
            if self._secret:
                return jwt.decode(
                    token,
                    self._secret,
                    algorithms=["HS256"],
                    audience=self._audience,
                    issuer=issuer,
                    options={"require": _REQUIRED_CLAIMS},
                )
            if self._jwks_client is not None:
                signing_key = self._jwks_client.get_signing_key_from_jwt(token)
                return jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=_ASYMMETRIC_ALGORITHMS,
                    audience=self._audience,
                    issuer=issuer,
                    options={"require": _REQUIRED_CLAIMS},
                )
        except jwt.PyJWTError as exc:
            raise AuthenticationError("Invalid or expired token") from exc

        raise AuthenticationError(
            "Authentication is not configured (set SUPABASE_JWT_SECRET or SUPABASE_URL)"
        )
