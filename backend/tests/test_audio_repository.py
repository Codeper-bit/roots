import asyncpg
import pytest

import factories as f

from app.repositories.audio_repository import create_audio_asset


async def test_create_audio_asset(conn: asyncpg.Connection):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    audio = await create_audio_asset(
        conn,
        story_id=story_id,
        storage_key="stories/test/audio.webm",
        mime_type="audio/webm",
    )

    assert audio is not None
    assert audio["id"] is not None
    assert audio["story_id"] == story_id
    assert audio["storage_key"] == "stories/test/audio.webm"
    assert audio["mime_type"] == "audio/webm"
    assert audio["upload_status"] == "pending"
    assert audio["size_bytes"] is None
    assert audio["checksum"] is None
