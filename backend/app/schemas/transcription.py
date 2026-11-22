
from uuid import UUID

from pydantic import Field

from app.schemas.common import Schema


class TranscriptionCreate(Schema):
    participant_id: UUID
    story_id: UUID
    audio_asset_id: UUID
    language_code: str = Field(pattern=r"^[a-z]{2,3}$")
    created_by: UUID | None = None
