
from uuid import UUID

import asyncpg

from app.repositories import story_repository


async def create_story(
    conn: asyncpg.Connection,
    *,
    owner_id: UUID,
    title: str,
    source_language: str,
    description: str | None = None,
    visibility: str = "private",
) -> asyncpg.Record:
    """Create a story for a user."""

    return await story_repository.create_story(
        conn,
        owner_id=owner_id,
        title=title,
        source_language=source_language,
        description=description,
        visibility=visibility,
    )


async def get_story(
    conn: asyncpg.Connection,
    story_id: UUID,
    owner_id: UUID,
) -> asyncpg.Record | None:
    """Retrieve a story only if it belongs to the requesting user."""

    story = await story_repository.get_story_by_id(
        conn,
        story_id,
    )

    if story is None:
        return None

    if story["owner_id"] != owner_id:
        return None

    return story


async def list_stories(
    conn: asyncpg.Connection,
    owner_id: UUID,
) -> list[asyncpg.Record]:
    """List all non-deleted stories belonging to a user."""

    return await story_repository.list_user_stories(
        conn,
        owner_id,
    )


async def delete_story(
    conn: asyncpg.Connection,
    story_id: UUID,
    owner_id: UUID,
) -> asyncpg.Record | None:
    """Soft-delete a story belonging to a user."""

    return await story_repository.soft_delete_story(
        conn,
        story_id,
        owner_id,
    )
