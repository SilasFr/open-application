"""Request authentication.

SKELETON: for now the current user is taken from the ``X-User-Id`` header so the API
is exercisable end-to-end. Before launch this must be replaced with real verification
of the Supabase JWT from the ``Authorization: Bearer <token>`` header (validate the
signature and read ``sub`` as the user id). Tracked as part of the auth feature spec.
"""

from __future__ import annotations

from fastapi import Header

_DEMO_USER_ID = "00000000-0000-0000-0000-000000000000"


async def get_current_user_id(x_user_id: str | None = Header(default=None)) -> str:
    return x_user_id or _DEMO_USER_ID
