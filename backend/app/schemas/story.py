
from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.common import (
    Schema,
    StoryStatus,
    StoryVisibility,
    TimestampedSchema,
)


class StoryCreate(Schema):
    # Temporary until authentication supplies the owner ID.
    owner_id: UUID

    title: str = Field(min_length=1, max_length=200)
    source_language: str = Field(pattern=r"^[a-z]{2,3}$")
    description: str | None = Field(default=None, max_length=5000)
    visibility: StoryVisibility = "private"

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Title cannot be blank.")
        return value


class StoryRead(TimestampedSchema):
    owner_id: UUID
    title: str
    description: str | None
    source_language: str
    status: StoryStatus
    visibility: StoryVisibility
    deleted_at: datetime | None = None


class StoryList(Schema):
    stories: list[StoryRead]
    total: int = Field(ge=0)
