

from uuid import UUID

from pydantic import Field

from app.schemas.common import AudioUploadStatus, Schema, TimestampedSchema


class AudioCreate(Schema):
    story_id: UUID

    # Needed by the current service to enforce audio_storage consent.
    participant_id: UUID

    storage_key: str = Field(min_length=1, max_length=1024)
    mime_type: str = Field(pattern=r"^audio/[A-Za-z0-9.+-]+$")


class AudioUploadComplete(Schema):
    size_bytes: int = Field(gt=0)
    checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    duration_ms: int | None = Field(default=None, ge=0)


class AudioRead(TimestampedSchema):
    story_id: UUID
    storage_key: str
    mime_type: str
    size_bytes: int | None
    duration_ms: int | None
    checksum: str | None
    upload_status: AudioUploadStatus
