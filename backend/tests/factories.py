from datetime import datetime, timezone
from uuid import UUID, uuid4

import asyncpg


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def insert_user(conn: asyncpg.Connection, *, email: str | None = None) -> UUID:
    return await conn.fetchval(
        "INSERT INTO users (email, password_hash, display_name) VALUES ($1, $2, $3) RETURNING id",
        email or f"user-{uuid4().hex}@example.com",
        "not-a-real-hash",
        "Test User",
    )


async def insert_story(
    conn: asyncpg.Connection,
    owner_id: UUID,
    *,
    title: str = "A story",
    source_language: str = "yo",
    status: str = "draft",
    visibility: str = "private",
) -> UUID:
    return await conn.fetchval(
        """INSERT INTO stories (owner_id, title, source_language, status, visibility)
           VALUES ($1, $2, $3, $4, $5) RETURNING id""",
        owner_id, title, source_language, status, visibility,
    )


async def insert_participant(
    conn: asyncpg.Connection, story_id: UUID, *, role: str = "storyteller", user_id: UUID | None = None
) -> UUID:
    return await conn.fetchval(
        """INSERT INTO story_participants (story_id, user_id, display_name, role)
           VALUES ($1, $2, $3, $4) RETURNING id""",
        story_id, user_id, "Grandmother", role,
    )


async def insert_consent(
    conn: asyncpg.Connection,
    participant_id: UUID,
    *,
    purpose: str = "transcription",
    status: str = "granted",
    granted_at: datetime | None = None,
    withdrawn_at: datetime | None = None,
) -> UUID:
    if status in ("granted", "withdrawn") and granted_at is None:
        granted_at = _now()
    return await conn.fetchval(
        """INSERT INTO consent_records (participant_id, purpose, status, granted_at, withdrawn_at)
           VALUES ($1, $2, $3, $4, $5) RETURNING id""",
        participant_id, purpose, status, granted_at, withdrawn_at,
    )


async def insert_audio(
    conn: asyncpg.Connection,
    story_id: UUID,
    *,
    upload_status: str = "pending",
    size_bytes: int | None = None,
    checksum: str | None = None,
    storage_key: str | None = None,
) -> UUID:
    return await conn.fetchval(
        """INSERT INTO audio_assets (story_id, storage_key, mime_type, size_bytes, checksum, upload_status)
           VALUES ($1, $2, 'audio/webm', $3, $4, $5) RETURNING id""",
        story_id, storage_key or f"stories/{uuid4().hex}/original.webm", size_bytes, checksum, upload_status,
    )


async def insert_version(
    conn: asyncpg.Connection,
    story_id: UUID,
    *,
    content_type: str = "transcript",
    language_code: str = "yo",
    version_number: int = 1,
    content: str = "Draft text",
    origin: str = "ai_generated",
    based_on_version_id: UUID | None = None,
    created_by: UUID | None = None,
    review_status: str = "unreviewed",
) -> UUID:
    return await conn.fetchval(
        """INSERT INTO content_versions
               (story_id, content_type, language_code, version_number, content,
                origin, based_on_version_id, created_by, review_status)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) RETURNING id""",
        story_id, content_type, language_code, version_number, content,
        origin, based_on_version_id, created_by, review_status,
    )


async def insert_review(
    conn: asyncpg.Connection, version_id: UUID, reviewer_id: UUID, *, decision: str = "approved"
) -> UUID:
    return await conn.fetchval(
        """INSERT INTO content_reviews (content_version_id, reviewer_id, decision)
           VALUES ($1, $2, $3) RETURNING id""",
        version_id, reviewer_id, decision,
    )


async def insert_job(
    conn: asyncpg.Connection,
    story_id: UUID,
    *,
    job_type: str = "translation",
    status: str = "queued",
    audio_asset_id: UUID | None = None,
    completed_at: datetime | None = None,
) -> UUID:
    return await conn.fetchval(
        """INSERT INTO processing_jobs (story_id, audio_asset_id, job_type, status, completed_at)
           VALUES ($1, $2, $3, $4, $5) RETURNING id""",
        story_id, audio_asset_id, job_type, status, completed_at,
    )


async def insert_question(conn: asyncpg.Connection, story_id: UUID, *, status: str = "suggested") -> UUID:
    return await conn.fetchval(
        "INSERT INTO story_questions (story_id, question, status) VALUES ($1, $2, $3) RETURNING id",
        story_id, "Where did your mother grow up?", status,
    )
