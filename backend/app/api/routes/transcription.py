
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.dependencies import get_db_connection
from app.schemas.content import ContentVersionRead
from app.schemas.transcription import TranscriptionCreate
from app.services import transcription_service


router = APIRouter(tags=["transcription"])


@router.post(
    "/transcriptions",
    response_model=ContentVersionRead,
    status_code=status.HTTP_201_CREATED,
)
async def transcribe_audio(
    data: TranscriptionCreate,
    request: Request,
    conn: asyncpg.Connection = Depends(get_db_connection),
):
    engine = getattr(request.app.state, "transcription_engine", None)

    if engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Transcription provider is not configured.",
        )

    try:
        return await transcription_service.transcribe_audio(
            conn,
            participant_id=data.participant_id,
            story_id=data.story_id,
            audio_asset_id=data.audio_asset_id,
            language_code=data.language_code,
            transcription_engine=engine,
            created_by=data.created_by,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
