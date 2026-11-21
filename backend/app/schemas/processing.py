
from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import (
    ProcessingJobStatus,
    ProcessingJobType,
    Schema,
)


class ProcessingJobCreate(Schema):
    story_id: UUID
    job_type: ProcessingJobType
    audio_asset_id: UUID | None = None


class ProcessingJobStatusUpdate(Schema):
    status: ProcessingJobStatus
    error_message: str | None = None


class ProcessingJobRead(Schema):
    id: UUID
    story_id: UUID
    audio_asset_id: UUID | None
    job_type: ProcessingJobType
    status: ProcessingJobStatus
    attempts: int = Field(ge=0)
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
