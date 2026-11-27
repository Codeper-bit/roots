"""Story-level authorization.

Every record in Roots hangs off a story, and a story belongs to one owner. These
helpers resolve a record to its story and confirm the authenticated profile owns
it. They answer 404 for both "doesn't exist" and "belongs to someone else", so
identifiers cannot be probed.

Identity always comes from the verified Supabase token (see
``auth_dependencies.get_current_profile``) and never from the request body or
query string. Fields such as ``owner_id``, ``created_by`` and ``reviewer_id`` are
still accepted for backward compatibility, but only if they match the caller.
"""

from __future__ import annotations

from uuid import UUID

import asyncpg

from app.core.errors import ForbiddenError, NotFoundError, UnprocessableError


def ensure_self(claimed: UUID | None, profile: asyncpg.Record, field: str) -> UUID:
    """Return the caller's id; reject a client-supplied id that differs from it."""
    if claimed is not None and claimed != profile["id"]:
        raise ForbiddenError(f"{field} must be your own user id.")
    return profile["id"]


async def require_story(
    conn: asyncpg.Connection,
    story_id: UUID,
    profile: asyncpg.Record,
) -> asyncpg.Record:
    story = await conn.fetchrow(
        """
        SELECT *
        FROM stories
        WHERE id = $1
          AND owner_id = $2
          AND deleted_at IS NULL
        """,
        story_id,
        profile["id"],
    )
    if story is None:
        raise NotFoundError("Story not found.")
    return story


async def require_participant(
    conn: asyncpg.Connection,
    participant_id: UUID,
    profile: asyncpg.Record,
) -> asyncpg.Record:
    participant = await conn.fetchrow(
        """
        SELECT p.*
        FROM story_participants p
        JOIN stories s ON s.id = p.story_id
        WHERE p.id = $1
          AND s.owner_id = $2
          AND s.deleted_at IS NULL
        """,
        participant_id,
        profile["id"],
    )
    if participant is None:
        raise NotFoundError("Participant not found.")
    return participant


async def require_participant_in_story(
    conn: asyncpg.Connection,
    participant_id: UUID,
    story_id: UUID,
    profile: asyncpg.Record,
) -> asyncpg.Record:
    """The caller owns the story AND the participant belongs to that story."""
    await require_story(conn, story_id, profile)
    participant = await require_participant(conn, participant_id, profile)
    if participant["story_id"] != story_id:
        raise UnprocessableError("That participant does not belong to this story.")
    return participant


async def require_consent(
    conn: asyncpg.Connection,
    consent_id: UUID,
    profile: asyncpg.Record,
) -> asyncpg.Record:
    consent = await conn.fetchrow(
        """
        SELECT c.*
        FROM consent_records c
        JOIN story_participants p ON p.id = c.participant_id
        JOIN stories s ON s.id = p.story_id
        WHERE c.id = $1
          AND s.owner_id = $2
          AND s.deleted_at IS NULL
        """,
        consent_id,
        profile["id"],
    )
    if consent is None:
        raise NotFoundError("Consent record not found.")
    return consent


async def require_audio_asset(
    conn: asyncpg.Connection,
    audio_asset_id: UUID,
    profile: asyncpg.Record,
) -> asyncpg.Record:
    asset = await conn.fetchrow(
        """
        SELECT a.*
        FROM audio_assets a
        JOIN stories s ON s.id = a.story_id
        WHERE a.id = $1
          AND s.owner_id = $2
          AND s.deleted_at IS NULL
        """,
        audio_asset_id,
        profile["id"],
    )
    if asset is None:
        raise NotFoundError("Audio asset not found.")
    return asset


async def require_content_version(
    conn: asyncpg.Connection,
    content_version_id: UUID,
    profile: asyncpg.Record,
) -> asyncpg.Record:
    version = await conn.fetchrow(
        """
        SELECT v.*
        FROM content_versions v
        JOIN stories s ON s.id = v.story_id
        WHERE v.id = $1
          AND s.owner_id = $2
          AND s.deleted_at IS NULL
        """,
        content_version_id,
        profile["id"],
    )
    if version is None:
        raise NotFoundError("Content version not found.")
    return version


async def require_processing_job(
    conn: asyncpg.Connection,
    job_id: UUID,
    profile: asyncpg.Record,
) -> asyncpg.Record:
    job = await conn.fetchrow(
        """
        SELECT j.*
        FROM processing_jobs j
        JOIN stories s ON s.id = j.story_id
        WHERE j.id = $1
          AND s.owner_id = $2
          AND s.deleted_at IS NULL
        """,
        job_id,
        profile["id"],
    )
    if job is None:
        raise NotFoundError("Processing job not found.")
    return job


async def require_story_question(
    conn: asyncpg.Connection,
    question_id: UUID,
    profile: asyncpg.Record,
) -> asyncpg.Record:
    question = await conn.fetchrow(
        """
        SELECT q.*
        FROM story_questions q
        JOIN stories s ON s.id = q.story_id
        WHERE q.id = $1
          AND s.owner_id = $2
          AND s.deleted_at IS NULL
        """,
        question_id,
        profile["id"],
    )
    if question is None:
        raise NotFoundError("Story question not found.")
    return question
