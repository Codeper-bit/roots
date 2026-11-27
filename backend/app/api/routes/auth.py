from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth_dependencies import get_supabase_user
from app.api.dependencies import get_db_connection
from app.schemas.auth import AuthProfileCreate, AuthProfileRead

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/me")
async def get_me(user=Depends(get_supabase_user)) -> dict[str, str | None]:
    """Return identity claims from a token already verified by Supabase Auth."""
    return {"id": str(user.id), "email": user.email}


@router.post(
    "/profile",
    response_model=AuthProfileRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_or_get_profile(
    payload: AuthProfileCreate,
    user=Depends(get_supabase_user),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> asyncpg.Record:
    """Create the Roots profile for the verified Supabase user.

    The email and Supabase UUID come from the verified token, never the request body.
    A legacy Roots row with the same email can be linked without copying passwords.
    """
    if not getattr(user, "email_confirmed_at", None):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Confirm your email address before creating your Roots profile.",
        )

    if not user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your Supabase account does not have an email address.",
        )

    auth_id = UUID(str(user.id))
    email = user.email.strip().lower()
    display_name = payload.display_name.strip()
    if not display_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Display name cannot be blank.",
        )

    async with conn.transaction():
        existing = await conn.fetchrow(
            "SELECT * FROM users WHERE supabase_auth_id = $1 FOR UPDATE",
            auth_id,
        )
        if existing:
            return existing

        legacy = await conn.fetchrow(
            "SELECT * FROM users WHERE email = $1 AND supabase_auth_id IS NULL FOR UPDATE",
            email,
        )
        if legacy:
            return await conn.fetchrow(
                """
                UPDATE users
                SET supabase_auth_id = $1,
                    display_name = $2,
                    password_hash = NULL
                WHERE id = $3
                RETURNING *
                """,
                auth_id,
                display_name,
                legacy["id"],
            )

        created = await conn.fetchrow(
            """
            INSERT INTO users (supabase_auth_id, email, password_hash, display_name)
            VALUES ($1, $2, NULL, $3)
            ON CONFLICT DO NOTHING
            RETURNING *
            """,
            auth_id,
            email,
            display_name,
        )
        if created:
            return created

        # ON CONFLICT DO NOTHING keeps the transaction usable for this lookup.
        existing = await conn.fetchrow(
            "SELECT * FROM users WHERE supabase_auth_id = $1",
            auth_id,
        )
        if existing:
            return existing
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists. Contact support to link it.",
        )
