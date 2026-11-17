
from uuid import UUID

import asyncpg


async def create_participant(
    conn: asyncpg.Connection,
    *,
    story_id: UUID,
    display_name: str,
    role: str,
    user_id: UUID | None = None,
) -> asyncpg.Record:
    query = """
        INSERT INTO story_participants (
            story_id,
            user_id,
            display_name,
            role
        )
        VALUES ($1, $2, $3, $4)
        RETURNING *
    """

    return await conn.fetchrow(
        query,
        story_id,
        user_id,
        display_name,
        role,
    )


async def get_participant_by_id(
    conn: asyncpg.Connection,
    participant_id: UUID,
) -> asyncpg.Record | None:
    query = """
        SELECT *
        FROM story_participants
        WHERE id = $1
    """

    return await conn.fetchrow(query, participant_id)


async def list_story_participants(
    conn: asyncpg.Connection,
    story_id: UUID,
) -> list[asyncpg.Record]:
    query = """
        SELECT *
        FROM story_participants
        WHERE story_id = $1
        ORDER BY created_at ASC
    """

    return await conn.fetch(query, story_id)


async def update_participant(
    conn: asyncpg.Connection,
    participant_id: UUID,
    story_id: UUID,
    *,
    display_name: str | None = None,
    role: str | None = None,
) -> asyncpg.Record | None:
    if display_name is None and role is None:
        raise ValueError("Provide at least one field to update")

    query = """
        UPDATE story_participants
        SET
            display_name = COALESCE($3, display_name),
            role = COALESCE($4, role),
            updated_at = NOW()
        WHERE id = $1
          AND story_id = $2
        RETURNING *
    """

    return await conn.fetchrow(
        query,
        participant_id,
        story_id,
        display_name,
        role,
    )
