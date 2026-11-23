
import logging
from uuid import UUID, uuid4

import asyncpg
from supabase import Client

from app.repositories import audio_repository
from app.services import consent_service, storage_service


logger = logging.getLogger(__name__)


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


async def upload_audio_asset(
    conn: asyncpg.Connection,
    *,
    participant_id: UUID,
    story_id: UUID,
    audio_data: bytes,
    mime_type: str,
    storage_client: Client,
    bucket_name: str,
    duration_ms: int | None = None,
) -> asyncpg.Record:
    """Coordinate consent, database metadata, and supabase audio upload."""

    await consent_service.require_active_consent(
        conn,
        participant_id,
        "audio_storage",
    )

    if not audio_data:
        raise ValueError("Audio file cannot be empty.")

    storage_key = f"stories/{story_id}/audio/{uuid4()}"

    audio_asset = await audio_repository.create_audio_asset(
        conn,
        story_id,
        storage_key,
        mime_type,
    )

    audio_asset_id = audio_asset["id"]

    try:
        size_bytes, checksum = await storage_service.upload_audio(
            storage_client,
            bucket_name=bucket_name,
            storage_key=storage_key,
            audio_data=audio_data,
            mime_type=mime_type,
        )

        uploaded_asset = await mark_audio_uploaded(
            conn,
            participant_id=participant_id,
            audio_asset_id=audio_asset_id,
            size_bytes=size_bytes,
            checksum=checksum,
            duration_ms=duration_ms,
        )

        if uploaded_asset is None:
            raise RuntimeError(
                "Could not update audio asset after storage upload."
            )

        return uploaded_asset

    except Exception:
        # Remove the object if it was uploaded but the database update failed.
        try:
            await storage_service.delete_audio(
                storage_client,
                bucket_name=bucket_name,
                storage_key=storage_key,
            )
        except Exception:
            logger.exception(
                "Could not clean up audio object %s",
                storage_key,
            )

        try:
            await audio_repository.mark_audio_asset_failed(
                conn,
                audio_asset_id,
            )
        except Exception:
            logger.exception(
                "Could not mark audio asset %s as failed",
                audio_asset_id,
            )

        raise


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
