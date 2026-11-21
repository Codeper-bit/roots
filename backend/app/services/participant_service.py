from uuid import UUID

import asyncpg

from app.repositories import story_participant_repository


async def create_participant(
    conn: asyncpg.Connection,
    *,
    story_id: UUID,
    display_name: str,
    role: str,
    user_id: UUID | None = None,
) -> asyncpg.Record:
    return await story_participant_repository.create_participant(
        conn,
        story_id=story_id,
        display_name=display_name,
        role=role,
        user_id=user_id,
    )


async def get_participant(
    conn: asyncpg.Connection,
    participant_id: UUID,
) -> asyncpg.Record | None:
    return await story_participant_repository.get_participant_by_id(
        conn, participant_id
    )


async def list_participants(
    conn: asyncpg.Connection,
    story_id: UUID,
) -> list[asyncpg.Record]:
    return await story_participant_repository.list_story_participants(
        conn, story_id
    )


async def update_participant(
    conn: asyncpg.Connection,
    participant_id: UUID,
    story_id: UUID,
    *,
    display_name: str | None = None,
    role: str | None = None,
) -> asyncpg.Record | None:
    return await story_participant_repository.update_participant(
        conn,
        participant_id,
        story_id,
        display_name=display_name,
        role=role,
    )
