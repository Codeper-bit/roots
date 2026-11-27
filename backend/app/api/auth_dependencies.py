"""Supabase access-token verification for protected API routes."""
from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID

import asyncpg
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

try:  # supabase-py >= 2.16 renamed the package
    from supabase_auth.errors import AuthApiError
except ImportError:  # pragma: no cover
    from gotrue.errors import AuthApiError

from app.api.dependencies import get_db_connection

_bearer = HTTPBearer(auto_error=False)


async def get_supabase_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> Any:
    """Verify the bearer token with Supabase Auth; never trust decoded JWT claims."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    client = getattr(request.app.state, "storage_client", None)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is unavailable.",
        )

    try:
        result = await asyncio.to_thread(
            client.auth.get_user,
            credentials.credentials,
        )
        user = result.user
        if user is None:
            raise ValueError("No user returned")
        # Parse here so malformed IDs cannot reach database queries.
        UUID(str(user.id))
        return user
    except (AuthApiError, ValueError, TypeError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except Exception:
        # Do not leak provider responses, tokens, or internal exception details.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not verify the access token. Try again.",
        ) from None


async def get_current_profile(
    user: Any = Depends(get_supabase_user),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> asyncpg.Record:
    """Resolve a verified Supabase identity to its Roots application profile."""
    profile = await conn.fetchrow(
        """
        SELECT id, email, display_name, created_at, updated_at
        FROM users
        WHERE supabase_auth_id = $1
        """,
        UUID(str(user.id)),
    )
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Complete your Roots profile before using the application.",
        )
    return profile
