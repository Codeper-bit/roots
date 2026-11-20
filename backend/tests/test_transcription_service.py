
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services import transcription_service


@pytest.fixture
def conn():
    return AsyncMock()


@pytest.fixture
def participant_id():
    return uuid4()


@pytest.fixture
def story_id():
    return uuid4()


@pytest.fixture
def audio_asset_id():
    return uuid4()


@pytest.fixture
def job_id():
    return uuid4()


@pytest.fixture
def audio_asset(story_id, audio_asset_id):
    return {
        "id": audio_asset_id,
        "story_id": story_id,
        "storage_key": "audio/test.mp3",
        "mime_type": "audio/mpeg",
        "upload_status": "uploaded",
    }


@pytest.fixture
def dependencies(monkeypatch):
    consent = AsyncMock()
    get_audio = AsyncMock()
    create_job = AsyncMock(return_value={"id": uuid4()})
    get_latest = AsyncMock(return_value=None)
    create_version = AsyncMock(return_value={"id": uuid4()})
    update_job = AsyncMock()

    monkeypatch.setattr(
        transcription_service.consent_service,
        "require_active_consent",
        consent,
    )

    monkeypatch.setattr(
        transcription_service.audio_service,
        "get_audio_asset",
        get_audio,
    )

    monkeypatch.setattr(
        transcription_service.processing_service,
        "create_processing_job",
        create_job,
    )

    monkeypatch.setattr(
        transcription_service.processing_service,
        "update_processing_job_status",
        update_job,
    )

    monkeypatch.setattr(
        transcription_service.content_version_repository,
        "get_latest_content_version",
        get_latest,
    )

    monkeypatch.setattr(
        transcription_service.content_version_repository,
        "create_content_version",
        create_version,
    )

    return {
        "consent": consent,
        "get_audio": get_audio,
        "create_job": create_job,
        "get_latest": get_latest,
        "create_version": create_version,
        "update_job": update_job,
    }


@pytest.mark.asyncio
async def test_transcribe_audio_success(
    conn,
    participant_id,
    story_id,
    audio_asset_id,
    audio_asset,
    dependencies,
):
    job_id = uuid4()
    expected = {"id": uuid4(), "content_type": "transcript"}

    dependencies["get_audio"].return_value = audio_asset
    dependencies["create_job"].return_value = {"id": job_id}
    dependencies["get_latest"].return_value = None
    dependencies["create_version"].return_value = expected

    engine = AsyncMock(return_value="Hello, this is a transcript.")

    result = await transcription_service.transcribe_audio(
        conn,
        participant_id=participant_id,
        story_id=story_id,
        audio_asset_id=audio_asset_id,
        language_code="en",
        transcription_engine=engine,
    )

    dependencies["consent"].assert_awaited_once_with(
        conn,
        participant_id,
        "transcription",
    )

    dependencies["get_audio"].assert_awaited_once_with(
        conn,
        audio_asset_id,
    )

    dependencies["create_job"].assert_awaited_once_with(
        conn,
        story_id,
        "transcription",
        audio_asset_id,
    )

    engine.assert_awaited_once_with(
        audio_asset=audio_asset,
        language_code="en",
    )

    dependencies["create_version"].assert_awaited_once_with(
        conn,
        story_id,
        "transcript",
        "en",
        1,
        "Hello, this is a transcript.",
        "ai_generated",
        created_by=None,
    )

    dependencies["update_job"].assert_awaited_once_with(
        conn,
        job_id,
        "succeeded",
    )

    assert result == expected


@pytest.mark.asyncio
async def test_transcribe_audio_uses_next_version_number(
    conn,
    participant_id,
    story_id,
    audio_asset_id,
    audio_asset,
    dependencies,
):
    dependencies["get_audio"].return_value = audio_asset
    dependencies["get_latest"].return_value = {
        "version_number": 3,
    }

    engine = AsyncMock(return_value="New transcript.")

    await transcription_service.transcribe_audio(
        conn,
        participant_id=participant_id,
        story_id=story_id,
        audio_asset_id=audio_asset_id,
        language_code="en",
        transcription_engine=engine,
    )

    assert dependencies["create_version"].await_args.args == (
        conn,
        story_id,
        "transcript",
        "en",
        4,
        "New transcript.",
        "ai_generated",
    )


@pytest.mark.asyncio
async def test_transcribe_audio_without_consent(
    conn,
    participant_id,
    story_id,
    audio_asset_id,
    dependencies,
):
    dependencies["consent"].side_effect = PermissionError(
        "Transcription consent required."
    )

    engine = AsyncMock()

    with pytest.raises(PermissionError):
        await transcription_service.transcribe_audio(
            conn,
            participant_id=participant_id,
            story_id=story_id,
            audio_asset_id=audio_asset_id,
            language_code="en",
            transcription_engine=engine,
        )

    dependencies["get_audio"].assert_not_awaited()
    dependencies["create_job"].assert_not_awaited()
    engine.assert_not_awaited()


@pytest.mark.asyncio
async def test_transcribe_audio_when_asset_does_not_exist(
    conn,
    participant_id,
    story_id,
    audio_asset_id,
    dependencies,
):
    dependencies["get_audio"].return_value = None

    engine = AsyncMock()

    with pytest.raises(ValueError, match="Audio asset not found"):
        await transcription_service.transcribe_audio(
            conn,
            participant_id=participant_id,
            story_id=story_id,
            audio_asset_id=audio_asset_id,
            language_code="en",
            transcription_engine=engine,
        )

    dependencies["create_job"].assert_not_awaited()
    engine.assert_not_awaited()


@pytest.mark.asyncio
async def test_transcribe_audio_asset_belongs_to_another_story(
    conn,
    participant_id,
    story_id,
    audio_asset_id,
    dependencies,
):
    dependencies["get_audio"].return_value = {
        "id": audio_asset_id,
        "story_id": uuid4(),
        "upload_status": "uploaded",
    }

    engine = AsyncMock()

    with pytest.raises(ValueError, match="does not belong to this story"):
        await transcription_service.transcribe_audio(
            conn,
            participant_id=participant_id,
            story_id=story_id,
            audio_asset_id=audio_asset_id,
            language_code="en",
            transcription_engine=engine,
        )

    dependencies["create_job"].assert_not_awaited()
    engine.assert_not_awaited()


@pytest.mark.asyncio
async def test_transcribe_audio_asset_not_uploaded(
    conn,
    participant_id,
    story_id,
    audio_asset_id,
    dependencies,
):
    dependencies["get_audio"].return_value = {
        "id": audio_asset_id,
        "story_id": story_id,
        "upload_status": "pending",
    }

    engine = AsyncMock()

    with pytest.raises(ValueError, match="not been uploaded"):
        await transcription_service.transcribe_audio(
            conn,
            participant_id=participant_id,
            story_id=story_id,
            audio_asset_id=audio_asset_id,
            language_code="en",
            transcription_engine=engine,
        )

    dependencies["create_job"].assert_not_awaited()
    engine.assert_not_awaited()


@pytest.mark.asyncio
async def test_transcribe_audio_engine_failure(
    conn,
    participant_id,
    story_id,
    audio_asset_id,
    audio_asset,
    dependencies,
):
    job_id = uuid4()

    dependencies["get_audio"].return_value = audio_asset
    dependencies["create_job"].return_value = {"id": job_id}

    engine = AsyncMock(
        side_effect=RuntimeError("Transcription provider failed")
    )

    with pytest.raises(
        RuntimeError,
        match="Transcription provider failed",
    ):
        await transcription_service.transcribe_audio(
            conn,
            participant_id=participant_id,
            story_id=story_id,
            audio_asset_id=audio_asset_id,
            language_code="en",
            transcription_engine=engine,
        )

    dependencies["create_version"].assert_not_awaited()

    dependencies["update_job"].assert_awaited_once_with(
        conn,
        job_id,
        "failed",
        "Transcription provider failed",
    )


@pytest.mark.asyncio
async def test_transcribe_audio_rejects_empty_result(
    conn,
    participant_id,
    story_id,
    audio_asset_id,
    audio_asset,
    dependencies,
):
    job_id = uuid4()

    dependencies["get_audio"].return_value = audio_asset
    dependencies["create_job"].return_value = {"id": job_id}

    engine = AsyncMock(return_value="   ")

    with pytest.raises(ValueError, match="empty or invalid text"):
        await transcription_service.transcribe_audio(
            conn,
            participant_id=participant_id,
            story_id=story_id,
            audio_asset_id=audio_asset_id,
            language_code="en",
            transcription_engine=engine,
        )

    dependencies["create_version"].assert_not_awaited()

    dependencies["update_job"].assert_awaited_once_with(
        conn,
        job_id,
        "failed",
        "Transcription engine returned empty or invalid text.",
    )
