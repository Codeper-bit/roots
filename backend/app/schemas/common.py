
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


StoryStatus = Literal["draft", "processing", "in_review", "completed"]
StoryVisibility = Literal["private", "family"]

ParticipantRole = Literal[
    "storyteller",
    "interviewer",
    "family_member",
    "translator",
    "reviewer",
    "other",
]

ConsentPurpose = Literal[
    "audio_storage",
    "transcription",
    "translation",
    "cultural_interpretation",
    "family_sharing",
]

ConsentStatus = Literal["granted", "declined", "withdrawn"]
ConsentDecision = Literal["granted", "declined"]

AudioUploadStatus = Literal["pending", "uploaded", "failed"]

ContentType = Literal["transcript", "translation", "interpretation"]
ContentOrigin = Literal["ai_generated", "human_created", "human_edited"]

ReviewStatus = Literal[
    "unreviewed",
    "approved",
    "rejected",
    "changes_requested",
]

ReviewDecision = Literal["approved", "rejected", "changes_requested"]

ProcessingJobType = Literal[
    "transcription",
    "translation",
    "interpretation",
    "question_generation",
]

ProcessingJobStatus = Literal[
    "queued",
    "running",
    "succeeded",
    "failed",
    "cancelled",
]

StoryQuestionStatus = Literal["suggested", "asked", "dismissed"]


class TimestampedSchema(Schema):
    id: UUID
    created_at: datetime
    updated_at: datetime
