
from uuid import uuid4

import pytest

from tests import factories as f
from app.repositories.audio_repository import (
    create_audio_asset,
    get_audio_asset_by_id,
)


@pytest.mark.asyncio
async def test_create_audio_asset(conn):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    audio = await create_audio_asset(
        conn=conn,
        story_id=story_id,
        storage_key="audio/test.mp3",
        mime_type="audio/mpeg",
    )

    assert audio is not None
    assert audio["story_id"] == story_id
    assert audio["storage_key"] == "audio/test.mp3"
    assert audio["mime_type"] == "audio/mpeg"


@pytest.mark.asyncio
async def test_get_audio_asset_by_id(conn):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    audio = await create_audio_asset(
        conn=conn,
        story_id=story_id,
        storage_key="audio/test.mp3",
        mime_type="audio/mpeg",
    )

    result = await get_audio_asset_by_id(
        conn=conn,
        audio_asset_id=audio["id"],
    )

    assert result is not None
    assert result["id"] == audio["id"]
    assert result["story_id"] == story_id


@pytest.mark.asyncio
async def test_get_audio_asset_by_id_not_found(conn):
    result = await get_audio_asset_by_id(
        conn=conn,
        audio_asset_id=uuid4(),
    )

    assert result is None
