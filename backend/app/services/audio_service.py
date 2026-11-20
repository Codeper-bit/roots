
import asyncpg
from uuid import UUID

from app.repositories import audio_repository
from app.services import consent_service


async def create_audio_asset(
    conn: asyncpg.Connection,
    *,
    participant_id: UUID,
    story_id: UUID,
    storage_key: str,
    mime_type: str,
) -> asyncpg.Record:

    await consent_service.require_active_consent(
        conn,
        participant_id,
        "audio_storage",
    )

    return await audio_repository.create_audio_asset(
        conn,
        story_id,
        storage_key,
        mime_type,
    )


async def get_audio_asset(
    conn: asyncpg.Connection,
    audio_asset_id: UUID,
) -> asyncpg.Record | None:

    return await audio_repository.get_audio_asset_by_id(
        conn,
        audio_asset_id,
    )


async def mark_audio_uploaded(
    conn: asyncpg.Connection,
    *,
    participant_id: UUID,
    audio_asset_id: UUID,
    size_bytes: int,
    checksum: str,
    duration_ms: int | None = None,
) -> asyncpg.Record | None:

    await consent_service.require_active_consent(
        conn,
        participant_id,
        "audio_storage",
    )

    return await audio_repository.mark_audio_asset_uploaded(
        conn,
        audio_asset_id,
        size_bytes=size_bytes,
        checksum=checksum,
        duration_ms=duration_ms,
    )


async def mark_audio_failed(
    conn: asyncpg.Connection,
    audio_asset_id: UUID,
) -> asyncpg.Record | None:

    return await audio_repository.mark_audio_asset_failed(
        conn,
        audio_asset_id,
    )
