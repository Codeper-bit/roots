

from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_db_connection
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
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ProcessingJobRead:
    job = await processing_service.create_processing_job(
        conn,
        story_id=payload.story_id,
        job_type=payload.job_type,
        audio_asset_id=payload.audio_asset_id,
    )

    return job


@router.get(
    "/{processing_job_id}",
    response_model=ProcessingJobRead,
)
async def get_processing_job(
    processing_job_id: UUID,
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ProcessingJobRead:
    job = await processing_service.get_processing_job(
        conn, processing_job_id
    )

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processing job not found.",
        )

    return job


@router.get(
    "/story/{story_id}",
    response_model=list[ProcessingJobRead],
)
async def get_story_processing_jobs(
    story_id: UUID,
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> list[ProcessingJobRead]:
    return await processing_service.get_story_processing_jobs(
        conn, story_id
    )


@router.patch(
    "/{processing_job_id}/status",
    response_model=ProcessingJobRead,
)
async def update_processing_job_status(
    processing_job_id: UUID,
    payload: ProcessingJobStatusUpdate,
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ProcessingJobRead:
    job = await processing_service.update_processing_job_status(
        conn,
        processing_job_id,
        payload.status,
        payload.error_message,
    )

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processing job not found.",
        )

    return job
