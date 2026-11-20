
import asyncpg
from uuid import UUID

from app.repositories import processing_job_repository


async def create_processing_job(
    conn: asyncpg.Connection,
    story_id: UUID,
    job_type: str,
    audio_asset_id: UUID | None = None,
) -> asyncpg.Record:
    return await processing_job_repository.create_processing_job(
        conn,
        story_id,
        job_type,
        audio_asset_id,
    )


async def get_processing_job(
    conn: asyncpg.Connection,
    processing_job_id: UUID,
) -> asyncpg.Record | None:
    return await processing_job_repository.get_processing_job_by_id(
        conn,
        processing_job_id,
    )


async def get_story_processing_jobs(
    conn: asyncpg.Connection,
    story_id: UUID,
) -> list[asyncpg.Record]:
    return await processing_job_repository.get_processing_jobs_by_story_id(
        conn,
        story_id,
    )


async def get_next_queued_job(
    conn: asyncpg.Connection,
) -> asyncpg.Record | None:
    return await processing_job_repository.get_next_queued_processing_job(
        conn,
    )


async def update_processing_job_status(
    conn: asyncpg.Connection,
    processing_job_id: UUID,
    status: str,
    error_message: str | None = None,
) -> asyncpg.Record | None:
    return await processing_job_repository.update_processing_job_status(
        conn,
        processing_job_id,
        status,
        error_message,
    )


async def get_jobs_by_status(
    conn: asyncpg.Connection,
    status: str,
) -> list[asyncpg.Record]:
    return await processing_job_repository.get_processing_jobs_by_status(
        conn,
        status,
    )
