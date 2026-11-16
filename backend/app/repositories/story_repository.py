
from uuid import UUID

import asyncpg


async def create_story(
    conn: asyncpg.Connection,
    *,
    owner_id: UUID,
    title: str,
    source_language: str,
    description: str | None = None,
    visibility: str = "private",
) -> asyncpg.Record:
    query = """
        INSERT INTO stories (
            owner_id,
            title,
            description,
            source_language,
            visibility
        )
        VALUES ($1, $2, $3, $4, $5)
        RETURNING *
    """

    return await conn.fetchrow(
        query,
        owner_id,
        title,
        description,
        source_language,
        visibility,
    )


async def get_story_by_id(
    conn: asyncpg.Connection,
    story_id: UUID,
) -> asyncpg.Record | None:
    query = """
        SELECT *
        FROM stories
        WHERE id = $1
          AND deleted_at IS NULL
    """

    return await conn.fetchrow(query, story_id)


async def list_user_stories(
    conn: asyncpg.Connection,
    owner_id: UUID,
) -> list[asyncpg.Record]:
    query = """
        SELECT *
        FROM stories
        WHERE owner_id = $1
          AND deleted_at IS NULL
        ORDER BY created_at DESC
    """

    return await conn.fetch(query, owner_id)


async def soft_delete_story(
    conn: asyncpg.Connection,
    story_id: UUID,
    owner_id: UUID,
) -> asyncpg.Record | None:
    query = """
        UPDATE stories
        SET deleted_at = NOW()
        WHERE id = $1
          AND owner_id = $2
          AND deleted_at IS NULL
        RETURNING *
    """

    return await conn.fetchrow(query, story_id, owner_id)
