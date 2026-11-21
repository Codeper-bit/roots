
from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.common import Schema, StoryQuestionStatus


class StoryQuestionCreate(Schema):
    story_id: UUID
    question: str = Field(min_length=1, max_length=1000)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Question cannot be blank.")
        return value


class StoryQuestionStatusUpdate(Schema):
    status: StoryQuestionStatus


class StoryQuestionRead(Schema):
    id: UUID
    story_id: UUID
    question: str
    status: StoryQuestionStatus
    created_at: datetime
    updated_at: datetime


class StoryQuestionList(Schema):
    questions: list[StoryQuestionRead]
