
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_db_connection
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
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ContentVersionRead:
    try:
        version = await content_service.create_content_version(
            conn,
            story_id=payload.story_id,
            content_type=payload.content_type,
            language_code=payload.language_code,
            content=payload.content,
            origin=payload.origin,
            based_on_version_id=payload.based_on_version_id,
            created_by=payload.created_by,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return version


@router.get(
    "/content-versions/{content_version_id}",
    response_model=ContentVersionRead,
)
async def get_content_version(
    content_version_id: UUID,
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ContentVersionRead:
    version = await content_service.get_content_version(
        conn, content_version_id
    )

    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content version not found.",
        )

    return version


@router.get(
    "/stories/{story_id}/content-versions",
    response_model=list[ContentVersionRead],
)
async def get_story_content_versions(
    story_id: UUID,
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> list[ContentVersionRead]:
    return await content_service.get_story_content_versions(
        conn, story_id
    )


@router.get(
    "/stories/{story_id}/content/latest",
    response_model=ContentVersionRead,
)
async def get_latest_content(
    story_id: UUID,
    content_type: str = Query(...),
    language_code: str = Query(...),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ContentVersionRead:
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No matching content version found.",
        )

    return version
