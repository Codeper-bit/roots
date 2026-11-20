
import pytest
from unittest.mock import AsyncMock
from uuid import UUID

from app.repositories import story_repository
from app.services import story_service


@pytest.fixture
def conn():
    return object()


@pytest.mark.asyncio
async def test_create_story(conn, monkeypatch):
    owner_id = UUID(int=1)

    expected_story = {
        "id": UUID(int=2),
        "owner_id": owner_id,
        "title": "Grandma's Story",
        "source_language": "yor",
        "visibility": "private",
    }

    mock_create = AsyncMock(return_value=expected_story)

    monkeypatch.setattr(
        story_repository,
        "create_story",
        mock_create,
    )

    result = await story_service.create_story(
        conn,
        owner_id=owner_id,
        title="Grandma's Story",
        source_language="yor",
    )

    assert result == expected_story

    mock_create.assert_awaited_once_with(
        conn,
        owner_id=owner_id,
        title="Grandma's Story",
        source_language="yor",
        description=None,
        visibility="private",
    )


@pytest.mark.asyncio
async def test_get_story(conn, monkeypatch):
    owner_id = UUID(int=1)
    story_id = UUID(int=2)

    expected_story = {
        "id": story_id,
        "owner_id": owner_id,
        "title": "Grandma's Story",
    }

    mock_get = AsyncMock(return_value=expected_story)

    monkeypatch.setattr(
        story_repository,
        "get_story_by_id",
        mock_get,
    )

    result = await story_service.get_story(
        conn,
        story_id,
        owner_id,
    )

    assert result == expected_story

    mock_get.assert_awaited_once_with(
        conn,
        story_id,
    )


@pytest.mark.asyncio
async def test_get_story_not_found(conn, monkeypatch):
    mock_get = AsyncMock(return_value=None)

    monkeypatch.setattr(
        story_repository,
        "get_story_by_id",
        mock_get,
    )

    result = await story_service.get_story(
        conn,
        UUID(int=2),
        UUID(int=1),
    )

    assert result is None


@pytest.mark.asyncio
async def test_get_story_rejects_wrong_owner(conn, monkeypatch):
    story = {
        "id": UUID(int=2),
        "owner_id": UUID(int=1),
        "title": "Grandma's Story",
    }

    mock_get = AsyncMock(return_value=story)

    monkeypatch.setattr(
        story_repository,
        "get_story_by_id",
        mock_get,
    )

    result = await story_service.get_story(
        conn,
        story["id"],
        UUID(int=3),
    )

    assert result is None


@pytest.mark.asyncio
async def test_list_stories(conn, monkeypatch):
    owner_id = UUID(int=1)

    expected_stories = [
        {
            "id": UUID(int=2),
            "owner_id": owner_id,
            "title": "First Story",
        },
        {
            "id": UUID(int=3),
            "owner_id": owner_id,
            "title": "Second Story",
        },
    ]

    mock_list = AsyncMock(return_value=expected_stories)

    monkeypatch.setattr(
        story_repository,
        "list_user_stories",
        mock_list,
    )

    result = await story_service.list_stories(
        conn,
        owner_id,
    )

    assert result == expected_stories
    assert len(result) == 2

    mock_list.assert_awaited_once_with(
        conn,
        owner_id,
    )


@pytest.mark.asyncio
async def test_delete_story(conn, monkeypatch):
    story_id = UUID(int=2)
    owner_id = UUID(int=1)

    expected_story = {
        "id": story_id,
        "owner_id": owner_id,
        "deleted_at": "2026-11-20",
    }

    mock_delete = AsyncMock(return_value=expected_story)

    monkeypatch.setattr(
        story_repository,
        "soft_delete_story",
        mock_delete,
    )

    result = await story_service.delete_story(
        conn,
        story_id,
        owner_id,
    )

    assert result == expected_story

    mock_delete.assert_awaited_once_with(
        conn,
        story_id,
        owner_id,
    )


@pytest.mark.asyncio
async def test_delete_story_not_found_or_not_owned(
    conn,
    monkeypatch,
):
    mock_delete = AsyncMock(return_value=None)

    monkeypatch.setattr(
        story_repository,
        "soft_delete_story",
        mock_delete,
    )

    result = await story_service.delete_story(
        conn,
        UUID(int=2),
        UUID(int=3),
    )

    assert result is None
