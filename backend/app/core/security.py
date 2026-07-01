"""Request authentication.

Extracts the Supabase access token from the ``Authorization: Bearer <token>``
header and verifies it via the injected :class:`TokenVerifier`. Failures raise
``AuthenticationError``, which the app maps to HTTP 401.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.dependencies import TokenVerifierDep
from app.domain.auth import AuthenticatedUser
from app.domain.exceptions import AuthenticationError

# auto_error=False so a missing/malformed header yields None (we raise our own
# AuthenticationError) rather than FastAPI's generic 403. Also documents the
# scheme in the OpenAPI "Authorize" dialog.
_bearer_scheme = HTTPBearer(auto_error=False)

CredentialsDep = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)]


async def get_current_user(
    credentials: CredentialsDep,
    verifier: TokenVerifierDep,
) -> AuthenticatedUser:
    if credentials is None or not credentials.credentials:
        raise AuthenticationError("Missing bearer token")
    return verifier.verify(credentials.credentials)


async def get_current_user_id(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> str:
    return user.id
