from uuid import UUID

from pydantic import Field

from app.schemas.common import Schema


class TranslationCreate(Schema):
    story_id: UUID
    participant_id: UUID
    source_version_id: UUID
    target_language_code: str = Field(
        pattern=r"^(en|yo|ha|ig)$"
    )
