
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.common import ParticipantRole, Schema, TimestampedSchema


class ParticipantCreate(Schema):
    story_id: UUID
    user_id: UUID | None = None
    display_name: str = Field(min_length=1, max_length=100)
    role: ParticipantRole

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Display name cannot be blank.")
        return value


class ParticipantRead(TimestampedSchema):
    story_id: UUID
    user_id: UUID | None
    display_name: str
    role: ParticipantRole


class ParticipantUpdate(Schema):
    display_name: str | None = Field(
        default=None, min_length=1, max_length=100)
    role: ParticipantRole | None = None

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Display name cannot be blank.")
        return value
