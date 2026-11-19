
import pytest

from tests import factories as f

from app.repositories.processing_job_repository import (
    create_processing_job,
)
from app.repositories.audio_repository import create_audio_asset

from app.repositories.processing_job_repository import (
    create_processing_job,
    get_processing_job_by_id,
)

from app.repositories.processing_job_repository import (
    create_processing_job,
    get_processing_job_by_id,
    get_processing_jobs_by_story_id,
    get_next_queued_processing_job,
    update_processing_job_status,
    get_processing_jobs_by_status,
)

from uuid import uuid4


@pytest.mark.asyncio
async def test_create_processing_job(conn):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    job = await create_processing_job(
        conn=conn,
        story_id=story_id,
        job_type="translation",
    )

    assert job is not None
    assert job["story_id"] == story_id
    assert job["audio_asset_id"] is None
    assert job["job_type"] == "translation"
    assert job["status"] == "queued"
    assert job["attempts"] == 0
    assert job["error_message"] is None
    assert job["completed_at"] is None


@pytest.mark.asyncio
async def test_create_transcription_job(conn):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    audio = await create_audio_asset(
        conn=conn,
        story_id=story_id,
        storage_key="audio/test-recording.mp3",
        mime_type="audio/mpeg",
    )

    job = await create_processing_job(
        conn=conn,
        story_id=story_id,
        audio_asset_id=audio["id"],
        job_type="transcription",
    )

    assert job is not None
    assert job["story_id"] == story_id
    assert job["audio_asset_id"] == audio["id"]
    assert job["job_type"] == "transcription"
    assert job["status"] == "queued"
    assert job["attempts"] == 0


@pytest.mark.asyncio
async def test_get_processing_job_by_id(conn):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    job = await create_processing_job(
        conn=conn,
        story_id=story_id,
        job_type="translation",
    )

    result = await get_processing_job_by_id(
        conn=conn,
        processing_job_id=job["id"],
    )

    assert result is not None
    assert result["id"] == job["id"]
    assert result["story_id"] == story_id
    assert result["job_type"] == "translation"


@pytest.mark.asyncio
async def test_get_processing_job_by_id_not_found(conn):
    result = await get_processing_job_by_id(
        conn=conn,
        processing_job_id=uuid4(),
    )

    assert result is None


@pytest.mark.asyncio
async def test_get_processing_jobs_by_story_id(conn):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    job1 = await create_processing_job(conn, story_id, "translation")
    job2 = await create_processing_job(conn, story_id, "interpretation")

    result = await get_processing_jobs_by_story_id(conn, story_id)

    assert len(result) == 2
    assert {job["id"] for job in result} == {
        job1["id"],
        job2["id"],
    }


@pytest.mark.asyncio
async def test_get_processing_jobs_by_story_id_empty(conn):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    result = await get_processing_jobs_by_story_id(conn, story_id)

    assert result == []


@pytest.mark.asyncio
async def test_get_next_queued_processing_job(conn):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    job = await create_processing_job(conn, story_id, "translation")

    result = await get_next_queued_processing_job(conn)

    assert result is not None
    assert result["id"] == job["id"]
    assert result["status"] == "queued"


@pytest.mark.asyncio
async def test_get_next_queued_processing_job_empty(conn):
    result = await get_next_queued_processing_job(conn)

    assert result is None


@pytest.mark.asyncio
async def test_update_processing_job_status(conn):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    job = await create_processing_job(conn, story_id, "translation")

    result = await update_processing_job_status(
        conn,
        job["id"],
        "running",
    )

    assert result is not None
    assert result["status"] == "running"
    assert result["completed_at"] is None


@pytest.mark.asyncio
async def test_update_processing_job_status_succeeded(conn):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    job = await create_processing_job(conn, story_id, "translation")

    result = await update_processing_job_status(
        conn,
        job["id"],
        "succeeded",
    )

    assert result is not None
    assert result["status"] == "succeeded"
    assert result["completed_at"] is not None


@pytest.mark.asyncio
async def test_update_processing_job_status_failed(conn):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    job = await create_processing_job(conn, story_id, "translation")

    result = await update_processing_job_status(
        conn,
        job["id"],
        "failed",
        "Translation failed",
    )

    assert result is not None
    assert result["status"] == "failed"
    assert result["error_message"] == "Translation failed"
    assert result["completed_at"] is not None


@pytest.mark.asyncio
async def test_update_processing_job_status_not_found(conn):
    from uuid import uuid4

    result = await update_processing_job_status(
        conn,
        uuid4(),
        "running",
    )

    assert result is None


@pytest.mark.asyncio
async def test_get_processing_jobs_by_status(conn):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    job1 = await create_processing_job(conn, story_id, "translation")
    job2 = await create_processing_job(conn, story_id, "interpretation")

    await update_processing_job_status(conn, job2["id"], "running")

    result = await get_processing_jobs_by_status(conn, "queued")

    assert len(result) == 1
    assert result[0]["id"] == job1["id"]


@pytest.mark.asyncio
async def test_get_processing_jobs_by_status_empty(conn):
    result = await get_processing_jobs_by_status(conn, "failed")

    assert result == []
