import asyncpg
from uuid import UUID


async def create_audio_asset(
    conn: asyncpg.Connection,
    story_id: UUID,
    storage_key: str,
    mime_type: str,
) -> asyncpg.Record:
    return await conn.fetchrow(
        """
        INSERT INTO audio_assets (
            story_id,
            storage_key,
            mime_type
        )
        VALUES ($1, $2, $3)
        RETURNING *;
        """,
        story_id,
        storage_key,
        mime_type,
    )
