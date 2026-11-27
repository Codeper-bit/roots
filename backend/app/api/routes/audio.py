import re
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

from app.api.auth_dependencies import get_current_profile
from app.api.authorization import require_audio_asset, require_participant_in_story
from app.api.dependencies import (
    get_db_connection,
    get_storage_bucket,
    get_storage_client,
)
from app.core.errors import ConflictError, UnprocessableError
from app.schemas.audio import AudioCreate, AudioRead, AudioUploadComplete
from app.services import audio_service

router = APIRouter(prefix="/audio-assets", tags=["audio"])

MAX_AUDIO_SIZE = 50 * 1024 * 1024  # 50 MB

# Matches the audio_assets.mime_type CHECK constraint.
_AUDIO_MIME_PATTERN = re.compile(r"^audio/[A-Za-z0-9.+-]+$")


def _bare_audio_mime_type(content_type: str | None) -> str | None:
    """'audio/webm;codecs=opus' -> 'audio/webm'; None if it isn't an audio type.

    Browsers append codec parameters to recorded blobs, but the database only
    accepts the bare media type.
    """
    bare = (content_type or "").split(";", 1)[0].strip().lower()
    return bare if _AUDIO_MIME_PATTERN.match(bare) else None


@router.post(
    "/upload",
    response_model=AudioRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_audio(
    story_id: UUID = Form(...),
    participant_id: UUID = Form(...),
    file: UploadFile = File(...),
    duration_ms: int | None = Form(default=None, ge=0),
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
    storage_client: Client = Depends(get_storage_client),
    bucket_name: str = Depends(get_storage_bucket),
) -> AudioRead:
    try:
        await require_participant_in_story(conn, participant_id, story_id, profile)

        mime_type = _bare_audio_mime_type(file.content_type)
        if mime_type is None:
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
                status_code=413,
                detail="Audio file exceeds the 50 MB limit.",
            )

        return await audio_service.upload_audio_asset(
            conn,
            participant_id=participant_id,
            story_id=story_id,
            audio_data=audio_data,
            mime_type=mime_type,
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
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> AudioRead:
    await require_participant_in_story(
        conn, payload.participant_id, payload.story_id, profile
    )

    # Without this, a caller could register ANOTHER story's object as their own
    # and have the service role transcribe it.
    if not payload.storage_key.startswith(f"stories/{payload.story_id}/audio/"):
        raise UnprocessableError(
            "storage_key must be inside this story's audio folder."
        )

    try:
        return await audio_service.create_audio_asset(
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


@router.get(
    "/{audio_asset_id}",
    response_model=AudioRead,
)
async def get_audio_asset(
    audio_asset_id: UUID,
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> AudioRead:
    return await require_audio_asset(conn, audio_asset_id, profile)


@router.post(
    "/{audio_asset_id}/complete",
    response_model=AudioRead,
)
async def complete_audio_upload(
    audio_asset_id: UUID,
    participant_id: UUID,
    payload: AudioUploadComplete,
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> AudioRead:
    asset = await require_audio_asset(conn, audio_asset_id, profile)
    await require_participant_in_story(conn, participant_id, asset["story_id"], profile)

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
        # It exists (checked above) but is no longer awaiting upload.
        raise ConflictError("This audio asset is not awaiting upload.")

    return audio_asset


@router.post(
    "/{audio_asset_id}/fail",
    response_model=AudioRead,
)
async def fail_audio_upload(
    audio_asset_id: UUID,
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> AudioRead:
    await require_audio_asset(conn, audio_asset_id, profile)

    audio_asset = await audio_service.mark_audio_failed(conn, audio_asset_id)

    if audio_asset is None:
        raise ConflictError("Only a pending upload can be marked as failed.")

    return audio_asset
