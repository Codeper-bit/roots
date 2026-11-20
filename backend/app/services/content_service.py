from uuid import UUID

import asyncpg

from app.repositories import (
    content_review_repository,
    content_version_repository,
)


CONTENT_TYPES = {
    "transcript",
    "translation",
    "interpretation",
}

CONTENT_ORIGINS = {
    "ai_generated",
    "human_created",
    "human_edited",
}

REVIEW_DECISIONS = {
    "approved",
    "rejected",
    "changes_requested",
}


async def create_content_version(
    conn: asyncpg.Connection,
    *,
    story_id: UUID,
    content_type: str,
    language_code: str,
    content: str,
    origin: str,
    based_on_version_id: UUID | None = None,
    created_by: UUID | None = None,
) -> asyncpg.Record:
    """Create a new immutable content version."""

    if content_type not in CONTENT_TYPES:
        raise ValueError("Invalid content type.")

    if origin not in CONTENT_ORIGINS:
        raise ValueError("Invalid content origin.")

    if not language_code.strip():
        raise ValueError("Language code cannot be empty.")

    if not content.strip():
        raise ValueError("Content cannot be empty.")

    if origin in {"human_created", "human_edited"} and created_by is None:
        raise ValueError("Human-created content requires a creator.")

    if origin == "human_edited":
        if based_on_version_id is None:
            raise ValueError("Human-edited content requires a base version.")

        base_version = (
            await content_version_repository.get_content_version_by_id(
                conn, based_on_version_id
            )
        )

        if base_version is None:
            raise ValueError("Base content version not found.")

        if base_version["story_id"] != story_id:
            raise ValueError("Base version belongs to another story.")

        if base_version["content_type"] != content_type:
            raise ValueError("Base version has a different content type.")

        if base_version["language_code"] != language_code:
            raise ValueError("Base version has a different language.")

    elif based_on_version_id is not None:
        raise ValueError(
            "Only human-edited content can have a base version."
        )

    latest = await content_version_repository.get_latest_content_version(
        conn,
        story_id,
        content_type,
        language_code,
    )

    version_number = (
        latest["version_number"] + 1
        if latest is not None
        else 1
    )

    return await content_version_repository.create_content_version(
        conn,
        story_id,
        content_type,
        language_code,
        version_number,
        content.strip(),
        origin,
        based_on_version_id=based_on_version_id,
        created_by=created_by,
    )


async def get_content_version(
    conn: asyncpg.Connection,
    content_version_id: UUID,
) -> asyncpg.Record | None:
    """Retrieve one content version."""

    return await content_version_repository.get_content_version_by_id(
        conn, content_version_id
    )


async def get_story_content_versions(
    conn: asyncpg.Connection,
    story_id: UUID,
) -> list[asyncpg.Record]:
    """Retrieve all content versions belonging to a story."""

    return await content_version_repository.get_content_versions_by_story_id(
        conn, story_id
    )


async def get_latest_content(
    conn: asyncpg.Connection,
    *,
    story_id: UUID,
    content_type: str,
    language_code: str,
) -> asyncpg.Record | None:
    """Retrieve the latest version for a content type and language."""

    if content_type not in CONTENT_TYPES:
        raise ValueError("Invalid content type.")

    return await content_version_repository.get_latest_content_version(
        conn,
        story_id,
        content_type,
        language_code,
    )


async def review_content(
    conn: asyncpg.Connection,
    *,
    content_version_id: UUID,
    reviewer_id: UUID,
    decision: str,
    comment: str | None = None,
) -> asyncpg.Record | None:
    """Submit a review and update the version's review status."""

    if decision not in REVIEW_DECISIONS:
        raise ValueError("Invalid review decision.")

    return await content_review_repository.create_content_review(
        conn,
        content_version_id,
        reviewer_id,
        decision,
        comment,
    )


async def get_content_reviews(
    conn: asyncpg.Connection,
    content_version_id: UUID,
) -> list[asyncpg.Record]:
    """Retrieve all reviews for a content version."""

    return await content_review_repository.get_content_reviews_by_version_id(
        conn, content_version_id
    )


async def get_reviewer_history(
    conn: asyncpg.Connection,
    reviewer_id: UUID,
) -> list[asyncpg.Record]:
    """Retrieve all reviews submitted by a reviewer."""

    return await content_review_repository.get_content_reviews_by_reviewer_id(
        conn, reviewer_id
    )
