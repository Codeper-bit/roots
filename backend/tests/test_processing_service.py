
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services import processing_service


@pytest.fixture
def conn():
    return AsyncMock()


@pytest.fixture
def story_id():
    return uuid4()


@pytest.fixture
def processing_job_id():
    return uuid4()


@pytest.fixture
def audio_asset_id():
    return uuid4()


@pytest.mark.asyncio
async def test_create_processing_job(
    conn,
    story_id,
    audio_asset_id,
    monkeypatch,
):
    expected = {"id": uuid4(), "status": "queued"}
    create_job = AsyncMock(return_value=expected)

    monkeypatch.setattr(
        processing_service.processing_job_repository,
        "create_processing_job",
        create_job,
    )

    result = await processing_service.create_processing_job(
        conn,
        story_id,
        "transcription",
        audio_asset_id,
    )

    create_job.assert_awaited_once_with(
        conn,
        story_id,
        "transcription",
        audio_asset_id,
    )
    assert result == expected


@pytest.mark.asyncio
async def test_create_processing_job_without_audio_asset(
    conn,
    story_id,
    monkeypatch,
):
    expected = {"id": uuid4(), "status": "queued"}
    create_job = AsyncMock(return_value=expected)

    monkeypatch.setattr(
        processing_service.processing_job_repository,
        "create_processing_job",
        create_job,
    )

    result = await processing_service.create_processing_job(
        conn,
        story_id,
        "question_generation",
    )

    create_job.assert_awaited_once_with(
        conn,
        story_id,
        "question_generation",
        None,
    )
    assert result == expected


@pytest.mark.asyncio
async def test_get_processing_job(
    conn,
    processing_job_id,
    monkeypatch,
):
    expected = {"id": processing_job_id}
    get_job = AsyncMock(return_value=expected)

    monkeypatch.setattr(
        processing_service.processing_job_repository,
        "get_processing_job_by_id",
        get_job,
    )

    result = await processing_service.get_processing_job(
        conn,
        processing_job_id,
    )

    get_job.assert_awaited_once_with(
        conn,
        processing_job_id,
    )
    assert result == expected


@pytest.mark.asyncio
async def test_get_processing_job_returns_none(
    conn,
    processing_job_id,
    monkeypatch,
):
    get_job = AsyncMock(return_value=None)

    monkeypatch.setattr(
        processing_service.processing_job_repository,
        "get_processing_job_by_id",
        get_job,
    )

    result = await processing_service.get_processing_job(
        conn,
        processing_job_id,
    )

    assert result is None


@pytest.mark.asyncio
async def test_get_story_processing_jobs(
    conn,
    story_id,
    monkeypatch,
):
    expected = [
        {"id": uuid4()},
        {"id": uuid4()},
    ]
    get_jobs = AsyncMock(return_value=expected)

    monkeypatch.setattr(
        processing_service.processing_job_repository,
        "get_processing_jobs_by_story_id",
        get_jobs,
    )

    result = await processing_service.get_story_processing_jobs(
        conn,
        story_id,
    )

    get_jobs.assert_awaited_once_with(conn, story_id)
    assert result == expected


@pytest.mark.asyncio
async def test_get_story_processing_jobs_returns_empty_list(
    conn,
    story_id,
    monkeypatch,
):
    get_jobs = AsyncMock(return_value=[])

    monkeypatch.setattr(
        processing_service.processing_job_repository,
        "get_processing_jobs_by_story_id",
        get_jobs,
    )

    result = await processing_service.get_story_processing_jobs(
        conn,
        story_id,
    )

    assert result == []


@pytest.mark.asyncio
async def test_get_next_queued_job(
    conn,
    monkeypatch,
):
    expected = {"id": uuid4(), "status": "queued"}
    get_next = AsyncMock(return_value=expected)

    monkeypatch.setattr(
        processing_service.processing_job_repository,
        "get_next_queued_processing_job",
        get_next,
    )

    result = await processing_service.get_next_queued_job(conn)

    get_next.assert_awaited_once_with(conn)
    assert result == expected


@pytest.mark.asyncio
async def test_get_next_queued_job_returns_none(
    conn,
    monkeypatch,
):
    get_next = AsyncMock(return_value=None)

    monkeypatch.setattr(
        processing_service.processing_job_repository,
        "get_next_queued_processing_job",
        get_next,
    )

    result = await processing_service.get_next_queued_job(conn)

    assert result is None


@pytest.mark.asyncio
async def test_update_processing_job_status(
    conn,
    processing_job_id,
    monkeypatch,
):
    expected = {"id": processing_job_id, "status": "running"}
    update_status = AsyncMock(return_value=expected)

    monkeypatch.setattr(
        processing_service.processing_job_repository,
        "update_processing_job_status",
        update_status,
    )

    result = await processing_service.update_processing_job_status(
        conn,
        processing_job_id,
        "running",
    )

    update_status.assert_awaited_once_with(
        conn,
        processing_job_id,
        "running",
        None,
    )
    assert result == expected


@pytest.mark.asyncio
async def test_update_processing_job_status_with_error(
    conn,
    processing_job_id,
    monkeypatch,
):
    expected = {
        "id": processing_job_id,
        "status": "failed",
        "error_message": "Processing failed",
    }
    update_status = AsyncMock(return_value=expected)

    monkeypatch.setattr(
        processing_service.processing_job_repository,
        "update_processing_job_status",
        update_status,
    )

    result = await processing_service.update_processing_job_status(
        conn,
        processing_job_id,
        "failed",
        "Processing failed",
    )

    update_status.assert_awaited_once_with(
        conn,
        processing_job_id,
        "failed",
        "Processing failed",
    )
    assert result == expected


@pytest.mark.asyncio
async def test_update_processing_job_status_returns_none(
    conn,
    processing_job_id,
    monkeypatch,
):
    update_status = AsyncMock(return_value=None)

    monkeypatch.setattr(
        processing_service.processing_job_repository,
        "update_processing_job_status",
        update_status,
    )

    result = await processing_service.update_processing_job_status(
        conn,
        processing_job_id,
        "running",
    )

    assert result is None


@pytest.mark.asyncio
async def test_get_jobs_by_status(
    conn,
    monkeypatch,
):
    expected = [
        {"id": uuid4(), "status": "queued"},
        {"id": uuid4(), "status": "queued"},
    ]
    get_jobs = AsyncMock(return_value=expected)

    monkeypatch.setattr(
        processing_service.processing_job_repository,
        "get_processing_jobs_by_status",
        get_jobs,
    )

    result = await processing_service.get_jobs_by_status(
        conn,
        "queued",
    )

    get_jobs.assert_awaited_once_with(conn, "queued")
    assert result == expected


@pytest.mark.asyncio
async def test_get_jobs_by_status_returns_empty_list(
    conn,
    monkeypatch,
):
    get_jobs = AsyncMock(return_value=[])

    monkeypatch.setattr(
        processing_service.processing_job_repository,
        "get_processing_jobs_by_status",
        get_jobs,
    )

    result = await processing_service.get_jobs_by_status(
        conn,
        "queued",
    )

    assert result == []
