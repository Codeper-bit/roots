from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.auth_dependencies import get_current_profile
from app.api.authorization import ensure_self, require_content_version, require_story
from app.api.dependencies import get_db_connection
from app.core.errors import NotFoundError
from app.schemas.content import ContentVersionCreate, ContentVersionRead
from app.services import content_service

router = APIRouter(tags=["content"])


@router.post(
    "/content-versions",
    response_model=ContentVersionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_content_version(
    payload: ContentVersionCreate,
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ContentVersionRead:
    await require_story(conn, payload.story_id, profile)
    created_by = ensure_self(payload.created_by, profile, "created_by")

    try:
        return await content_service.create_content_version(
            conn,
            story_id=payload.story_id,
            content_type=payload.content_type,
            language_code=payload.language_code,
            content=payload.content,
            origin=payload.origin,
            based_on_version_id=payload.based_on_version_id,
            created_by=created_by,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get(
    "/content-versions/{content_version_id}",
    response_model=ContentVersionRead,
)
async def get_content_version(
    content_version_id: UUID,
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ContentVersionRead:
    return await require_content_version(conn, content_version_id, profile)


@router.get(
    "/stories/{story_id}/content-versions",
    response_model=list[ContentVersionRead],
)
async def get_story_content_versions(
    story_id: UUID,
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> list[ContentVersionRead]:
    await require_story(conn, story_id, profile)
    return await content_service.get_story_content_versions(conn, story_id)


@router.get(
    "/stories/{story_id}/content/latest",
    response_model=ContentVersionRead,
)
async def get_latest_content(
    story_id: UUID,
    content_type: str = Query(...),
    language_code: str = Query(...),
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ContentVersionRead:
    await require_story(conn, story_id, profile)

    try:
        version = await content_service.get_latest_content(
            conn,
            story_id=story_id,
            content_type=content_type,
            language_code=language_code,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    if version is None:
        raise NotFoundError("No matching content version found.")

    return version
