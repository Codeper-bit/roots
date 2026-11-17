
from uuid import uuid4

import asyncpg

from app.repositories.story_participant_repository import (
    create_participant,
    get_participant_by_id,
    list_story_participants,
    update_participant,
)
from tests import factories as f


async def test_create_participant(conn: asyncpg.Connection) -> None:
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    participant = await create_participant(
        conn,
        story_id=story_id,
        display_name="Grandma Grace",
        role="storyteller",
    )

    assert participant["display_name"] == "Grandma Grace"
    assert participant["role"] == "storyteller"
    assert participant["story_id"] == story_id
    assert participant["user_id"] is None


async def test_create_participant_with_user_account(
    conn: asyncpg.Connection,
) -> None:
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)
    user_id = await f.insert_user(conn)

    participant = await create_participant(
        conn,
        story_id=story_id,
        user_id=user_id,
        display_name="Daniel",
        role="interviewer",
    )

    assert participant["user_id"] == user_id


async def test_get_participant_by_id(conn: asyncpg.Connection) -> None:
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    created = await create_participant(
        conn,
        story_id=story_id,
        display_name="Grace",
        role="storyteller",
    )

    participant = await get_participant_by_id(conn, created["id"])

    assert participant is not None
    assert participant["id"] == created["id"]


async def test_get_missing_participant_returns_none(
    conn: asyncpg.Connection,
) -> None:
    participant = await get_participant_by_id(conn, uuid4())

    assert participant is None


async def test_list_story_participants(conn: asyncpg.Connection) -> None:
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    first = await create_participant(
        conn,
        story_id=story_id,
        display_name="Grace",
        role="storyteller",
    )

    second = await create_participant(
        conn,
        story_id=story_id,
        display_name="Daniel",
        role="interviewer",
    )

    participants = await list_story_participants(conn, story_id)

    participant_ids = {p["id"] for p in participants}

    assert first["id"] in participant_ids
    assert second["id"] in participant_ids
    assert len(participants) == 2


async def test_list_participants_does_not_mix_stories(
    conn: asyncpg.Connection,
) -> None:
    owner = await f.insert_user(conn)
    story_a = await f.insert_story(conn, owner)
    story_b = await f.insert_story(conn, owner)

    await create_participant(
        conn,
        story_id=story_a,
        display_name="Grace",
        role="storyteller",
    )

    await create_participant(
        conn,
        story_id=story_b,
        display_name="Daniel",
        role="interviewer",
    )

    participants = await list_story_participants(conn, story_a)

    assert len(participants) == 1
    assert participants[0]["display_name"] == "Grace"


async def test_update_participant_name(conn: asyncpg.Connection) -> None:
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    created = await create_participant(
        conn,
        story_id=story_id,
        display_name="Grace",
        role="storyteller",
    )

    updated = await update_participant(
        conn,
        created["id"],
        story_id,
        display_name="Grandma Grace",
    )

    assert updated is not None
    assert updated["display_name"] == "Grandma Grace"
    assert updated["role"] == "storyteller"


async def test_update_participant_role(conn: asyncpg.Connection) -> None:
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    created = await create_participant(
        conn,
        story_id=story_id,
        display_name="Grace",
        role="storyteller",
    )

    updated = await update_participant(
        conn,
        created["id"],
        story_id,
        role="reviewer",
    )

    assert updated is not None
    assert updated["role"] == "reviewer"
    assert updated["display_name"] == "Grace"


async def test_update_cannot_target_another_story(
    conn: asyncpg.Connection,
) -> None:
    owner = await f.insert_user(conn)
    story_a = await f.insert_story(conn, owner)
    story_b = await f.insert_story(conn, owner)

    participant = await create_participant(
        conn,
        story_id=story_a,
        display_name="Grace",
        role="storyteller",
    )

    result = await update_participant(
        conn,
        participant["id"],
        story_b,
        display_name="Changed Name",
    )

    assert result is None
