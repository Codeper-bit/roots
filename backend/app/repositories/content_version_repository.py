
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


async def create_next_content_version(
    conn: asyncpg.Connection,
    story_id: UUID,
    content_type: str,
    language_code: str,
    content: str,
    origin: str,
    based_on_version_id: UUID | None = None,
    created_by: UUID | None = None,
) -> asyncpg.Record:
    """Insert the next version number for (story, type, language) atomically.

    Reading "latest + 1" and inserting in two steps lets two concurrent requests
    pick the same number; the second then fails on the UNIQUE constraint with a
    500. A transaction-scoped advisory lock keyed on the same tuple serialises
    them, so each gets its own consecutive number.
    """
    async with conn.transaction():
        await conn.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended($1, 0))",
            f"content_versions:{story_id}:{content_type}:{language_code}",
        )
        latest_number = await conn.fetchval(
            """
            SELECT COALESCE(MAX(version_number), 0)
            FROM content_versions
            WHERE story_id = $1
              AND content_type = $2
              AND language_code = $3;
            """,
            story_id,
            content_type,
            language_code,
        )
        return await create_content_version(
            conn,
            story_id,
            content_type,
            language_code,
            latest_number + 1,
            content,
            origin,
            based_on_version_id=based_on_version_id,
            created_by=created_by,
        )
