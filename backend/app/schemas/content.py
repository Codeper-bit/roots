

from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.schemas.common import (
    ContentOrigin,
    ContentType,
    ReviewDecision,
    ReviewStatus,
    Schema,
)


class ContentVersionCreate(Schema):
    story_id: UUID
    content_type: ContentType
    language_code: str = Field(pattern=r"^[a-z]{2,3}$")
    content: str = Field(min_length=1)
    origin: ContentOrigin
    based_on_version_id: UUID | None = None
    created_by: UUID | None = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Content cannot be blank.")
        return value

    @model_validator(mode="after")
    def validate_origin_fields(self):
        if self.origin in {"human_created", "human_edited"}:
            if self.created_by is None:
                raise ValueError("Human-created content requires created_by.")

        if self.origin == "human_edited" and self.based_on_version_id is None:
            raise ValueError(
                "Human-edited content requires based_on_version_id.")

        return self


class ContentVersionRead(Schema):
    id: UUID
    story_id: UUID
    content_type: ContentType
    language_code: str
    version_number: int = Field(ge=1)
    content: str
    origin: ContentOrigin
    based_on_version_id: UUID | None
    created_by: UUID | None
    review_status: ReviewStatus
    created_at: datetime
    updated_at: datetime


class ContentReviewCreate(Schema):
    content_version_id: UUID
    reviewer_id: UUID
    decision: ReviewDecision
    comment: str | None = Field(default=None, max_length=5000)


class ContentReviewRead(Schema):
    id: UUID
    content_version_id: UUID
    reviewer_id: UUID
    decision: ReviewDecision
    comment: str | None
    created_at: datetime


class ContentReviewList(Schema):
    reviews: list[ContentReviewRead]
