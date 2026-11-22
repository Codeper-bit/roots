
from datetime import datetime
from typing import Literal

from pydantic import ConfigDict

from pydantic import BaseModel


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TimestampedSchema(Schema):
    created_at: datetime
    updated_at: datetime


# Stories
StoryStatus = Literal[
    "draft",
    "processing",
    "in_review",
    "completed",
]

StoryVisibility = Literal[
    "private",
    "family",
]


# Participants
ParticipantRole = Literal[
    "storyteller",
    "interviewer",
    "family_member",
    "translator",
    "reviewer",
    "other",
]


# Consent
ConsentPurpose = Literal[
    "audio_storage",
    "transcription",
    "translation",
    "cultural_interpretation",
    "family_sharing",
]

ConsentStatus = Literal[
    "granted",
    "declined",
    "withdrawn",
]


# Audio
AudioUploadStatus = Literal[
    "pending",
    "uploaded",
    "failed",
]


# Processing
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


# Content
ContentType = Literal[
    "transcript",
    "translation",
    "interpretation",
]

ContentOrigin = Literal[
    "ai_generated",
    "human_created",
    "human_edited",
]

ReviewDecision = Literal[
    "approved",
    "rejected",
    "changes_requested",
]

ReviewStatus = Literal[
    "unreviewed",
    "approved",
    "rejected",
    "changes_requested",
]


# Story questions
StoryQuestionStatus = Literal[
    "suggested",
    "asked",
    "dismissed",
]
