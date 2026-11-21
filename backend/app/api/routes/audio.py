from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_db_connection
from app.schemas.audio import AudioCreate, AudioRead, AudioUploadComplete
from app.services import audio_service

router = APIRouter(prefix="/audio-assets", tags=["audio"])


@router.post(
    "",
    response_model=AudioRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_audio_asset(
    payload: AudioCreate,
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> AudioRead:
    try:
        audio_asset = await audio_service.create_audio_asset(
            conn,
            participant_id=payload.participant_id,
            story_id=payload.story_id,
            storage_key=payload.storage_key,
            mime_type=payload.mime_type,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )

    return audio_asset


@router.get(
    "/{audio_asset_id}",
    response_model=AudioRead,
)
async def get_audio_asset(
    audio_asset_id: UUID,
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> AudioRead:
    audio_asset = await audio_service.get_audio_asset(
        conn, audio_asset_id
    )

    if audio_asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio asset not found.",
        )

    return audio_asset


@router.post(
    "/{audio_asset_id}/complete",
    response_model=AudioRead,
)
async def complete_audio_upload(
    audio_asset_id: UUID,
    participant_id: UUID,
    payload: AudioUploadComplete,
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> AudioRead:
    try:
        audio_asset = await audio_service.mark_audio_uploaded(
            conn,
            participant_id=participant_id,
            audio_asset_id=audio_asset_id,
            size_bytes=payload.size_bytes,
            checksum=payload.checksum,
            duration_ms=payload.duration_ms,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )

    if audio_asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio asset not found.",
        )

    return audio_asset


@router.post(
    "/{audio_asset_id}/fail",
    response_model=AudioRead,
)
async def fail_audio_upload(
    audio_asset_id: UUID,
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> AudioRead:
    audio_asset = await audio_service.mark_audio_failed(
        conn, audio_asset_id
    )

    if audio_asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio asset not found.",
        )

    return audio_asset
