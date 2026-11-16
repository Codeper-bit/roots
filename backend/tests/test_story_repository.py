
from uuid import UUID

import asyncpg
import pytest

from app.repositories.story_repository import (
    create_story,
    get_story_by_id,
    list_user_stories,
    soft_delete_story,
)
from tests import factories as f


async def test_create_story(conn: asyncpg.Connection) -> None:
    owner_id = await f.insert_user(conn)

    story = await create_story(
        conn,
        owner_id=owner_id,
        title="My Grandmother's Story",
        description="A story about family history.",
        source_language="yo",
    )

    assert story is not None
    assert isinstance(story["id"], UUID)
    assert story["owner_id"] == owner_id
    assert story["title"] == "My Grandmother's Story"
    assert story["description"] == "A story about family history."
    assert story["source_language"] == "yo"
    assert story["status"] == "draft"
    assert story["visibility"] == "private"
    assert story["deleted_at"] is None


async def test_get_story_by_id(conn: asyncpg.Connection) -> None:
    owner_id = await f.insert_user(conn)
    story = await create_story(
        conn,
        owner_id=owner_id,
        title="Family Memories",
        source_language="ha",
    )

    result = await get_story_by_id(conn, story["id"])

    assert result is not None
    assert result["id"] == story["id"]
    assert result["title"] == "Family Memories"


async def test_get_story_by_id_returns_none_for_missing_story(
    conn: asyncpg.Connection,
) -> None:
    from uuid import uuid4

    result = await get_story_by_id(conn, uuid4())

    assert result is None


async def test_list_user_stories(conn: asyncpg.Connection) -> None:
    owner_id = await f.insert_user(conn)

    first = await create_story(
        conn,
        owner_id=owner_id,
        title="First Story",
        source_language="yo",
    )
    second = await create_story(
        conn,
        owner_id=owner_id,
        title="Second Story",
        source_language="ig",
    )

    stories = await list_user_stories(conn, owner_id)

    story_ids = {story["id"] for story in stories}

    assert len(stories) == 2
    assert first["id"] in story_ids
    assert second["id"] in story_ids


async def test_list_user_stories_does_not_return_other_users_stories(
    conn: asyncpg.Connection,
) -> None:
    owner_a = await f.insert_user(conn)
    owner_b = await f.insert_user(conn)

    await create_story(
        conn,
        owner_id=owner_a,
        title="A's Story",
        source_language="yo",
    )
    await create_story(
        conn,
        owner_id=owner_b,
        title="B's Story",
        source_language="ha",
    )

    stories = await list_user_stories(conn, owner_a)

    assert len(stories) == 1
    assert stories[0]["owner_id"] == owner_a


async def test_soft_delete_story(conn: asyncpg.Connection) -> None:
    owner_id = await f.insert_user(conn)

    story = await create_story(
        conn,
        owner_id=owner_id,
        title="Story to Delete",
        source_language="ig",
    )

    deleted = await soft_delete_story(
        conn,
        story["id"],
        owner_id,
    )

    assert deleted is not None
    assert deleted["deleted_at"] is not None

    # The row still exists in PostgreSQL.
    exists = await conn.fetchval(
        "SELECT EXISTS (SELECT 1 FROM stories WHERE id = $1)",
        story["id"],
    )

    assert exists is True


async def test_soft_deleted_story_is_not_retrieved(
    conn: asyncpg.Connection,
) -> None:
    owner_id = await f.insert_user(conn)

    story = await create_story(
        conn,
        owner_id=owner_id,
        title="Deleted Story",
        source_language="yo",
    )

    await soft_delete_story(conn, story["id"], owner_id)

    result = await get_story_by_id(conn, story["id"])

    assert result is None


async def test_soft_deleted_story_is_not_listed(
    conn: asyncpg.Connection,
) -> None:
    owner_id = await f.insert_user(conn)

    story = await create_story(
        conn,
        owner_id=owner_id,
        title="Deleted Story",
        source_language="ha",
    )

    await soft_delete_story(conn, story["id"], owner_id)

    stories = await list_user_stories(conn, owner_id)

    assert stories == []


async def test_user_cannot_delete_another_users_story(
    conn: asyncpg.Connection,
) -> None:
    owner_id = await f.insert_user(conn)
    another_user_id = await f.insert_user(conn)

    story = await create_story(
        conn,
        owner_id=owner_id,
        title="Private Story",
        source_language="yo",
    )

    result = await soft_delete_story(
        conn,
        story["id"],
        another_user_id,
    )

    assert result is None

    # The original story must remain active.
    assert await conn.fetchval(
        "SELECT deleted_at IS NULL FROM stories WHERE id = $1",
        story["id"],
    ) is True


async def test_soft_delete_cannot_be_repeated(
    conn: asyncpg.Connection,
) -> None:
    owner_id = await f.insert_user(conn)

    story = await create_story(
        conn,
        owner_id=owner_id,
        title="Another Story",
        source_language="ig",
    )

    first_delete = await soft_delete_story(
        conn, story["id"], owner_id
    )
    second_delete = await soft_delete_story(
        conn, story["id"], owner_id
    )

    assert first_delete is not None
    assert second_delete is None
