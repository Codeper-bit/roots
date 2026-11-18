
from uuid import uuid4

import pytest

from tests import factories as f

from app.repositories.content_version_repository import (
    create_content_version,
    get_content_version_by_id,
    get_content_versions_by_story_id,
    get_latest_content_version,
)


@pytest.mark.asyncio
async def test_create_content_version(conn):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    version = await create_content_version(
        conn=conn,
        story_id=story_id,
        content_type="transcript",
        language_code="yo",
        version_number=1,
        content="Bawo ni gbogbo eniyan.",
        origin="ai_generated",
    )

    assert version is not None
    assert version["story_id"] == story_id
    assert version["content_type"] == "transcript"
    assert version["language_code"] == "yo"
    assert version["version_number"] == 1
    assert version["content"] == "Bawo ni gbogbo eniyan."
    assert version["origin"] == "ai_generated"
    assert version["based_on_version_id"] is None
    assert version["created_by"] is None
    assert version["review_status"] == "unreviewed"


@pytest.mark.asyncio
async def test_get_content_version_by_id(conn):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    version = await create_content_version(
        conn=conn,
        story_id=story_id,
        content_type="transcript",
        language_code="yo",
        version_number=1,
        content="Bawo ni gbogbo eniyan.",
        origin="ai_generated",
    )

    result = await get_content_version_by_id(
        conn=conn,
        content_version_id=version["id"],
    )

    assert result is not None
    assert result["id"] == version["id"]
    assert result["story_id"] == story_id
    assert result["content"] == "Bawo ni gbogbo eniyan."


@pytest.mark.asyncio
async def test_get_content_version_by_id_not_found(conn):
    result = await get_content_version_by_id(
        conn=conn,
        content_version_id=uuid4(),
    )

    assert result is None


@pytest.mark.asyncio
async def test_get_content_versions_by_story_id(conn):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    first_version = await create_content_version(
        conn=conn,
        story_id=story_id,
        content_type="transcript",
        language_code="yo",
        version_number=1,
        content="First transcript.",
        origin="ai_generated",
    )

    second_version = await create_content_version(
        conn=conn,
        story_id=story_id,
        content_type="transcript",
        language_code="yo",
        version_number=2,
        content="Second transcript.",
        origin="ai_generated",
    )

    result = await get_content_versions_by_story_id(
        conn=conn,
        story_id=story_id,
    )

    assert len(result) == 2
    assert result[0]["id"] == first_version["id"]
    assert result[1]["id"] == second_version["id"]


@pytest.mark.asyncio
async def test_get_content_versions_by_story_id_empty(conn):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    result = await get_content_versions_by_story_id(
        conn=conn,
        story_id=story_id,
    )

    assert result == []


@pytest.mark.asyncio
async def test_get_latest_content_version(conn):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    await create_content_version(
        conn=conn,
        story_id=story_id,
        content_type="transcript",
        language_code="yo",
        version_number=1,
        content="First transcript.",
        origin="ai_generated",
    )

    second_version = await create_content_version(
        conn=conn,
        story_id=story_id,
        content_type="transcript",
        language_code="yo",
        version_number=2,
        content="Second transcript.",
        origin="ai_generated",
    )

    result = await get_latest_content_version(
        conn=conn,
        story_id=story_id,
        content_type="transcript",
        language_code="yo",
    )

    assert result is not None
    assert result["id"] == second_version["id"]
    assert result["version_number"] == 2
    assert result["content"] == "Second transcript."


@pytest.mark.asyncio
async def test_get_latest_content_version_not_found(conn):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    result = await get_latest_content_version(
        conn=conn,
        story_id=story_id,
        content_type="transcript",
        language_code="yo",
    )

    assert result is None


@pytest.mark.asyncio
async def test_create_human_edited_content_version(conn):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    original = await create_content_version(
        conn=conn,
        story_id=story_id,
        content_type="transcript",
        language_code="yo",
        version_number=1,
        content="Original transcript.",
        origin="ai_generated",
    )

    edited = await create_content_version(
        conn=conn,
        story_id=story_id,
        content_type="transcript",
        language_code="yo",
        version_number=2,
        content="Corrected transcript.",
        origin="human_edited",
        based_on_version_id=original["id"],
        created_by=owner,
    )

    assert edited["based_on_version_id"] == original["id"]
    assert edited["created_by"] == owner
    assert edited["version_number"] == 2
