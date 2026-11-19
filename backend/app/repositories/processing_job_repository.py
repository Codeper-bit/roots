
import asyncpg
from uuid import UUID


async def create_processing_job(
    conn: asyncpg.Connection,
    story_id: UUID,
    job_type: str,
    audio_asset_id: UUID | None = None,
) -> asyncpg.Record:
    return await conn.fetchrow(
        """
        INSERT INTO processing_jobs (
            story_id,
            audio_asset_id,
            job_type
        )
        VALUES ($1, $2, $3)
        RETURNING *;
        """,
        story_id,
        audio_asset_id,
        job_type,
    )


async def get_processing_job_by_id(
    conn: asyncpg.Connection,
    processing_job_id: UUID,
) -> asyncpg.Record | None:
    return await conn.fetchrow(
        """
        SELECT *
        FROM processing_jobs
        WHERE id = $1;
        """,
        processing_job_id,
    )


async def get_processing_jobs_by_story_id(
    conn: asyncpg.Connection,
    story_id: UUID,
) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT *
        FROM processing_jobs
        WHERE story_id = $1
        ORDER BY created_at DESC;
        """,
        story_id,
    )


async def get_next_queued_processing_job(
    conn: asyncpg.Connection,
) -> asyncpg.Record | None:
    return await conn.fetchrow(
        """
        SELECT *
        FROM processing_jobs
        WHERE status = 'queued'
        ORDER BY created_at ASC
        LIMIT 1;
        """
    )


async def update_processing_job_status(
    conn: asyncpg.Connection,
    processing_job_id: UUID,
    status: str,
    error_message: str | None = None,
) -> asyncpg.Record | None:
    return await conn.fetchrow(
        """
        UPDATE processing_jobs
        SET
            status = $2,
            error_message = $3,
            completed_at = CASE
                WHEN $2 IN ('succeeded', 'failed', 'cancelled')
                THEN now()
                ELSE NULL
            END
        WHERE id = $1
        RETURNING *;
        """,
        processing_job_id,
        status,
        error_message,
    )


async def get_processing_jobs_by_status(
    conn: asyncpg.Connection,
    status: str,
) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT *
        FROM processing_jobs
        WHERE status = $1
        ORDER BY created_at ASC;
        """,
        status,
    )
