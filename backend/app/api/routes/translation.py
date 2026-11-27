
import logging

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.auth_dependencies import get_current_profile
from app.api.dependencies import get_db_connection
from app.core.errors import DomainError
from app.schemas.content import ContentVersionRead
from app.schemas.translation import TranslationCreate
from app.services import story_service, translation_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["translation"])


@router.post(
    "/translations",
    response_model=ContentVersionRead,
    status_code=status.HTTP_201_CREATED,
)
async def translate_transcript(
    payload: TranslationCreate,
    request: Request,
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ContentVersionRead:

    # Resolve ownership from the authenticated profile, not the request body.
    story = await story_service.get_story(
        conn,
        payload.story_id,
        profile["id"],
    )

    if story is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story not found.",
        )

    engine = getattr(request.app.state, "translation_engine", None)

    if engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Translation provider is not configured.",
        )

    try:
        return await translation_service.translate_content(
            conn,
            story_id=payload.story_id,
            participant_id=payload.participant_id,
            source_version_id=payload.source_version_id,
            target_language_code=payload.target_language_code,
            translation_engine=engine,
            created_by=profile["id"],
        )

    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Participant has not granted translation consent.",
        ) from None

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except DomainError:
        raise  # carries a user-safe message and status; handled in main.py
    except Exception:
        logger.exception("Unexpected translation failure")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Translation failed. Please try again.",
        ) from None
