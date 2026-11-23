
from uuid import UUID

import asyncpg
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from supabase import Client

from app.api.dependencies import (
    get_db_connection,
    get_storage_bucket,
    get_storage_client,
)
from app.schemas.audio import AudioCreate, AudioRead, AudioUploadComplete
from app.services import audio_service


router = APIRouter(prefix="/audio-assets", tags=["audio"])

MAX_AUDIO_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post(
    "/upload",
    response_model=AudioRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_audio(
    story_id: UUID = Form(...),
    participant_id: UUID = Form(...),
    file: UploadFile = File(...),
    duration_ms: int | None = Form(default=None),
    conn: asyncpg.Connection = Depends(get_db_connection),
    storage_client: Client = Depends(get_storage_client),
    bucket_name: str = Depends(get_storage_bucket),
) -> AudioRead:
    try:
        if not file.content_type or not file.content_type.startswith("audio/"):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Only audio files are accepted.",
            )

        audio_data = await file.read(MAX_AUDIO_SIZE + 1)

        if not audio_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio file cannot be empty.",
            )

        if len(audio_data) > MAX_AUDIO_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail="Audio file exceeds the 50 MB limit.",
            )

        return await audio_service.upload_audio_asset(
            conn,
            participant_id=participant_id,
            story_id=story_id,
            audio_data=audio_data,
            mime_type=file.content_type,
            storage_client=storage_client,
            bucket_name=bucket_name,
            duration_ms=duration_ms,
        )

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    finally:
        await file.close()


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
        ) from exc

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
        ) from exc

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
