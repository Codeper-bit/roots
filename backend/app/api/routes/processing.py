from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, status

from app.api.auth_dependencies import get_current_profile
from app.api.authorization import require_processing_job, require_story
from app.api.dependencies import get_db_connection
from app.core.errors import NotFoundError
from app.schemas.processing import (
    ProcessingJobCreate,
    ProcessingJobRead,
    ProcessingJobStatusUpdate,
)
from app.services import processing_service

router = APIRouter(prefix="/processing-jobs", tags=["processing"])


@router.post(
    "",
    response_model=ProcessingJobRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_processing_job(
    payload: ProcessingJobCreate,
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ProcessingJobRead:
    await require_story(conn, payload.story_id, profile)

    return await processing_service.create_processing_job(
        conn,
        story_id=payload.story_id,
        job_type=payload.job_type,
        audio_asset_id=payload.audio_asset_id,
    )


@router.get(
    "/story/{story_id}",
    response_model=list[ProcessingJobRead],
)
async def get_story_processing_jobs(
    story_id: UUID,
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> list[ProcessingJobRead]:
    await require_story(conn, story_id, profile)
    return await processing_service.get_story_processing_jobs(conn, story_id)


@router.get(
    "/{processing_job_id}",
    response_model=ProcessingJobRead,
)
async def get_processing_job(
    processing_job_id: UUID,
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ProcessingJobRead:
    return await require_processing_job(conn, processing_job_id, profile)


@router.patch(
    "/{processing_job_id}/status",
    response_model=ProcessingJobRead,
)
async def update_processing_job_status(
    processing_job_id: UUID,
    payload: ProcessingJobStatusUpdate,
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ProcessingJobRead:
    await require_processing_job(conn, processing_job_id, profile)

    job = await processing_service.update_processing_job_status(
        conn,
        processing_job_id,
        payload.status,
        payload.error_message,
    )

    if job is None:
        raise NotFoundError("Processing job not found.")

    return job
