
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.story import StoryCreate, StoryRead
from app.schemas.participant import ParticipantCreate, ParticipantUpdate
from app.schemas.consent import ConsentCreate, ConsentRead
from app.schemas.audio import AudioCreate, AudioUploadComplete
from app.schemas.processing import ProcessingJobCreate, ProcessingJobStatusUpdate
from app.schemas.content import ContentVersionCreate, ContentReviewCreate
from app.schemas.story_question import (
    StoryQuestionCreate,
    StoryQuestionStatusUpdate,
)


# ---------------------------------------------------------------------
# STORY SCHEMAS
# ---------------------------------------------------------------------

def test_story_create_valid():
    schema = StoryCreate(
        owner_id=uuid4(),
        title="  My family story  ",
        source_language="yo",
        visibility="private",
    )

    assert schema.title == "My family story"
    assert schema.source_language == "yo"


def test_story_create_rejects_blank_title():
    with pytest.raises(ValidationError):
        StoryCreate(
            owner_id=uuid4(),
            title="   ",
            source_language="yo",
        )


def test_story_create_rejects_public_visibility():
    with pytest.raises(ValidationError):
        StoryCreate(
            owner_id=uuid4(),
            title="Family story",
            source_language="yo",
            visibility="public",
        )


# ---------------------------------------------------------------------
# PARTICIPANT SCHEMAS
# ---------------------------------------------------------------------

def test_participant_create_valid():
    schema = ParticipantCreate(
        story_id=uuid4(),
        display_name="  Grandmother  ",
        role="storyteller",
    )

    assert schema.display_name == "Grandmother"
    assert schema.user_id is None


def test_participant_create_rejects_invalid_role():
    with pytest.raises(ValidationError):
        ParticipantCreate(
            story_id=uuid4(),
            display_name="Grandmother",
            role="admin",
        )


def test_participant_update_valid():
    schema = ParticipantUpdate(display_name="New name")

    assert schema.display_name == "New name"


# ---------------------------------------------------------------------
# CONSENT SCHEMAS
# ---------------------------------------------------------------------

def test_consent_create_valid():
    schema = ConsentCreate(
        participant_id=uuid4(),
        purpose="audio_storage",
        status="granted",
    )

    assert schema.status == "granted"


def test_consent_create_rejects_withdrawn():
    # Withdrawal is an operation on an existing consent record.
    with pytest.raises(ValidationError):
        ConsentCreate(
            participant_id=uuid4(),
            purpose="audio_storage",
            status="withdrawn",
        )


def test_consent_create_rejects_invalid_purpose():
    with pytest.raises(ValidationError):
        ConsentCreate(
            participant_id=uuid4(),
            purpose="unknown",
            status="granted",
        )


# ---------------------------------------------------------------------
# AUDIO SCHEMAS
# ---------------------------------------------------------------------

def test_audio_create_valid():
    schema = AudioCreate(
        story_id=uuid4(),
        participant_id=uuid4(),
        storage_key="recordings/story-1/audio.webm",
        mime_type="audio/webm",
    )

    assert schema.mime_type == "audio/webm"


def test_audio_create_rejects_invalid_mime_type():
    with pytest.raises(ValidationError):
        AudioCreate(
            story_id=uuid4(),
            participant_id=uuid4(),
            storage_key="recordings/audio.webm",
            mime_type="video/mp4",
        )


def test_audio_upload_complete_valid():
    schema = AudioUploadComplete(
        size_bytes=1024,
        checksum="a" * 64,
        duration_ms=5000,
    )

    assert schema.size_bytes == 1024
    assert len(schema.checksum) == 64


def test_audio_upload_complete_rejects_bad_checksum():
    with pytest.raises(ValidationError):
        AudioUploadComplete(
            size_bytes=1024,
            checksum="not-a-valid-checksum",
        )


def test_audio_upload_complete_rejects_zero_size():
    with pytest.raises(ValidationError):
        AudioUploadComplete(
            size_bytes=0,
            checksum="a" * 64,
        )


# ---------------------------------------------------------------------
# PROCESSING SCHEMAS
# ---------------------------------------------------------------------

def test_processing_job_create_valid():
    schema = ProcessingJobCreate(
        story_id=uuid4(),
        job_type="transcription",
        audio_asset_id=uuid4(),
    )

    assert schema.job_type == "transcription"


def test_processing_job_create_rejects_invalid_type():
    with pytest.raises(ValidationError):
        ProcessingJobCreate(
            story_id=uuid4(),
            job_type="summarization",
        )


def test_processing_status_update_valid():
    schema = ProcessingJobStatusUpdate(
        status="failed",
        error_message="Processing failed",
    )

    assert schema.status == "failed"


# ---------------------------------------------------------------------
# CONTENT SCHEMAS
# ---------------------------------------------------------------------

def test_ai_content_version_create_valid():
    schema = ContentVersionCreate(
        story_id=uuid4(),
        content_type="transcript",
        language_code="yo",
        content="A family story.",
        origin="ai_generated",
    )

    assert schema.origin == "ai_generated"


def test_human_created_content_requires_creator():
    with pytest.raises(ValidationError):
        ContentVersionCreate(
            story_id=uuid4(),
            content_type="transcript",
            language_code="yo",
            content="A family story.",
            origin="human_created",
        )


def test_human_edited_content_requires_base_version():
    with pytest.raises(ValidationError):
        ContentVersionCreate(
            story_id=uuid4(),
            content_type="transcript",
            language_code="yo",
            content="Corrected story.",
            origin="human_edited",
            created_by=uuid4(),
        )


def test_human_edited_content_valid():
    schema = ContentVersionCreate(
        story_id=uuid4(),
        content_type="transcript",
        language_code="yo",
        content="Corrected story.",
        origin="human_edited",
        created_by=uuid4(),
        based_on_version_id=uuid4(),
    )

    assert schema.based_on_version_id is not None


def test_content_review_create_valid():
    schema = ContentReviewCreate(
        content_version_id=uuid4(),
        reviewer_id=uuid4(),
        decision="approved",
        comment="Reviewed.",
    )

    assert schema.decision == "approved"


def test_content_review_rejects_unreviewed():
    with pytest.raises(ValidationError):
        ContentReviewCreate(
            content_version_id=uuid4(),
            reviewer_id=uuid4(),
            decision="unreviewed",
        )


# ---------------------------------------------------------------------
# STORY QUESTION SCHEMAS
# ---------------------------------------------------------------------

def test_story_question_create_valid():
    schema = StoryQuestionCreate(
        story_id=uuid4(),
        question="What was your childhood like?",
    )

    assert schema.question == "What was your childhood like?"


def test_story_question_create_rejects_blank_question():
    with pytest.raises(ValidationError):
        StoryQuestionCreate(
            story_id=uuid4(),
            question="   ",
        )


def test_story_question_status_update_valid():
    schema = StoryQuestionStatusUpdate(status="asked")

    assert schema.status == "asked"


def test_story_question_status_update_rejects_invalid_status():
    with pytest.raises(ValidationError):
        StoryQuestionStatusUpdate(status="completed")
