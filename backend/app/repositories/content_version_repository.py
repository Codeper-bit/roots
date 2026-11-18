
import asyncpg
from uuid import UUID


async def create_content_version(
    conn: asyncpg.Connection,
    story_id: UUID,
    content_type: str,
    language_code: str,
    version_number: int,
    content: str,
    origin: str,
    based_on_version_id: UUID | None = None,
    created_by: UUID | None = None,
) -> asyncpg.Record:
    return await conn.fetchrow(
        """
        INSERT INTO content_versions (
            story_id,
            content_type,
            language_code,
            version_number,
            content,
            origin,
            based_on_version_id,
            created_by
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING *;
        """,
        story_id,
        content_type,
        language_code,
        version_number,
        content,
        origin,
        based_on_version_id,
        created_by,
    )


async def get_content_version_by_id(
    conn: asyncpg.Connection,
    content_version_id: UUID,
) -> asyncpg.Record | None:
    return await conn.fetchrow(
        """
        SELECT *
        FROM content_versions
        WHERE id = $1;
        """,
        content_version_id,
    )


async def get_content_versions_by_story_id(
    conn: asyncpg.Connection,
    story_id: UUID,
) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT *
        FROM content_versions
        WHERE story_id = $1
        ORDER BY content_type ASC,
                 language_code ASC,
                 version_number ASC;
        """,
        story_id,
    )


async def get_latest_content_version(
    conn: asyncpg.Connection,
    story_id: UUID,
    content_type: str,
    language_code: str,
) -> asyncpg.Record | None:
    return await conn.fetchrow(
        """
        SELECT *
        FROM content_versions
        WHERE story_id = $1
          AND content_type = $2
          AND language_code = $3
        ORDER BY version_number DESC
        LIMIT 1;
        """,
        story_id,
        content_type,
        language_code,
    )
