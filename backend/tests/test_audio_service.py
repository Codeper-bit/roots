
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services import audio_service


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


@pytest.mark.asyncio
async def test_create_audio_asset_checks_consent(
    conn,
    participant_id,
    story_id,
    monkeypatch,
):
    require_consent = AsyncMock()
    create_asset = AsyncMock(return_value={"id": uuid4()})

    monkeypatch.setattr(
        audio_service.consent_service,
        "require_active_consent",
        require_consent,
    )
    monkeypatch.setattr(
        audio_service.audio_repository,
        "create_audio_asset",
        create_asset,
    )

    result = await audio_service.create_audio_asset(
        conn,
        participant_id=participant_id,
        story_id=story_id,
        storage_key="audio/test.mp3",
        mime_type="audio/mpeg",
    )

    require_consent.assert_awaited_once_with(
        conn,
        participant_id,
        "audio_storage",
    )

    create_asset.assert_awaited_once_with(
        conn,
        story_id,
        "audio/test.mp3",
        "audio/mpeg",
    )

    assert result["id"] is not None


@pytest.mark.asyncio
async def test_create_audio_asset_stops_when_consent_is_missing(
    conn,
    participant_id,
    story_id,
    monkeypatch,
):
    require_consent = AsyncMock(
        side_effect=PermissionError("Audio storage consent required")
    )
    create_asset = AsyncMock()

    monkeypatch.setattr(
        audio_service.consent_service,
        "require_active_consent",
        require_consent,
    )
    monkeypatch.setattr(
        audio_service.audio_repository,
        "create_audio_asset",
        create_asset,
    )

    with pytest.raises(PermissionError):
        await audio_service.create_audio_asset(
            conn,
            participant_id=participant_id,
            story_id=story_id,
            storage_key="audio/test.mp3",
            mime_type="audio/mpeg",
        )

    create_asset.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_audio_asset(
    conn,
    audio_asset_id,
    monkeypatch,
):
    expected = {"id": audio_asset_id}
    get_asset = AsyncMock(return_value=expected)

    monkeypatch.setattr(
        audio_service.audio_repository,
        "get_audio_asset_by_id",
        get_asset,
    )

    result = await audio_service.get_audio_asset(
        conn,
        audio_asset_id,
    )

    get_asset.assert_awaited_once_with(
        conn,
        audio_asset_id,
    )

    assert result == expected


@pytest.mark.asyncio
async def test_get_audio_asset_returns_none(
    conn,
    audio_asset_id,
    monkeypatch,
):
    get_asset = AsyncMock(return_value=None)

    monkeypatch.setattr(
        audio_service.audio_repository,
        "get_audio_asset_by_id",
        get_asset,
    )

    result = await audio_service.get_audio_asset(
        conn,
        audio_asset_id,
    )

    assert result is None


@pytest.mark.asyncio
async def test_mark_audio_uploaded_checks_consent(
    conn,
    participant_id,
    audio_asset_id,
    monkeypatch,
):
    require_consent = AsyncMock()
    mark_uploaded = AsyncMock(
        return_value={"id": audio_asset_id, "upload_status": "uploaded"}
    )

    monkeypatch.setattr(
        audio_service.consent_service,
        "require_active_consent",
        require_consent,
    )
    monkeypatch.setattr(
        audio_service.audio_repository,
        "mark_audio_asset_uploaded",
        mark_uploaded,
    )

    result = await audio_service.mark_audio_uploaded(
        conn,
        participant_id=participant_id,
        audio_asset_id=audio_asset_id,
        size_bytes=1024,
        checksum="abc123",
        duration_ms=5000,
    )

    require_consent.assert_awaited_once_with(
        conn,
        participant_id,
        "audio_storage",
    )

    mark_uploaded.assert_awaited_once_with(
        conn,
        audio_asset_id,
        size_bytes=1024,
        checksum="abc123",
        duration_ms=5000,
    )

    assert result["upload_status"] == "uploaded"


@pytest.mark.asyncio
async def test_mark_audio_uploaded_stops_without_consent(
    conn,
    participant_id,
    audio_asset_id,
    monkeypatch,
):
    require_consent = AsyncMock(
        side_effect=PermissionError("Audio storage consent required")
    )
    mark_uploaded = AsyncMock()

    monkeypatch.setattr(
        audio_service.consent_service,
        "require_active_consent",
        require_consent,
    )
    monkeypatch.setattr(
        audio_service.audio_repository,
        "mark_audio_asset_uploaded",
        mark_uploaded,
    )

    with pytest.raises(PermissionError):
        await audio_service.mark_audio_uploaded(
            conn,
            participant_id=participant_id,
            audio_asset_id=audio_asset_id,
            size_bytes=1024,
            checksum="abc123",
        )

    mark_uploaded.assert_not_awaited()


@pytest.mark.asyncio
async def test_mark_audio_failed(
    conn,
    audio_asset_id,
    monkeypatch,
):
    expected = {"id": audio_asset_id, "upload_status": "failed"}
    mark_failed = AsyncMock(return_value=expected)

    monkeypatch.setattr(
        audio_service.audio_repository,
        "mark_audio_asset_failed",
        mark_failed,
    )

    result = await audio_service.mark_audio_failed(
        conn,
        audio_asset_id,
    )

    mark_failed.assert_awaited_once_with(
        conn,
        audio_asset_id,
    )

    assert result == expected


@pytest.mark.asyncio
async def test_mark_audio_failed_returns_none(
    conn,
    audio_asset_id,
    monkeypatch,
):
    mark_failed = AsyncMock(return_value=None)

    monkeypatch.setattr(
        audio_service.audio_repository,
        "mark_audio_asset_failed",
        mark_failed,
    )

    result = await audio_service.mark_audio_failed(
        conn,
        audio_asset_id,
    )

    assert result is None
