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


async def get_audio_asset_by_id(
    conn: asyncpg.Connection,
    audio_asset_id: UUID,
) -> asyncpg.Record | None:
    return await conn.fetchrow(
        """
        SELECT *
        FROM audio_assets
        WHERE id = $1;
        """,
        audio_asset_id,
    )


async def mark_audio_asset_uploaded(
    conn: asyncpg.Connection,
    audio_asset_id: UUID,
    *,
    size_bytes: int,
    checksum: str,
    duration_ms: int | None = None,
) -> asyncpg.Record | None:
    return await conn.fetchrow(
        """
        UPDATE audio_assets
        SET
            upload_status = 'uploaded',
            size_bytes = $2,
            checksum = $3,
            duration_ms = $4
        WHERE id = $1
          AND upload_status IN ('pending', 'failed')
        RETURNING *;
        """,
        audio_asset_id,
        size_bytes,
        checksum,
        duration_ms,
    )


async def mark_audio_asset_failed(
    conn: asyncpg.Connection,
    audio_asset_id: UUID,
) -> asyncpg.Record | None:
    return await conn.fetchrow(
        """
        UPDATE audio_assets
        SET upload_status = 'failed'
        WHERE id = $1
          AND upload_status = 'pending'
        RETURNING *;
        """,
        audio_asset_id,
    )
