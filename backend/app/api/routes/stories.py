from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, Response, status

from app.api.auth_dependencies import get_current_profile
from app.api.authorization import ensure_self
from app.api.dependencies import get_db_connection
from app.core.errors import NotFoundError
from app.schemas.story import StoryCreate, StoryList, StoryRead
from app.services import story_service

router = APIRouter(prefix="/stories", tags=["stories"])


@router.post(
    "",
    response_model=StoryRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_story(
    payload: StoryCreate,
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> StoryRead:
    """Create a story owned by the authenticated user."""

    return await story_service.create_story(
        conn,
        owner_id=ensure_self(payload.owner_id, profile, "owner_id"),
        title=payload.title,
        source_language=payload.source_language,
        description=payload.description,
        visibility=payload.visibility,
    )


@router.get(
    "",
    response_model=StoryList,
    status_code=status.HTTP_200_OK,
)
async def list_stories(
    owner_id: UUID | None = None,
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> StoryList:
    """List the authenticated user's non-deleted stories."""

    stories = await story_service.list_stories(
        conn,
        ensure_self(owner_id, profile, "owner_id"),
    )

    return {
        "stories": stories,
        "total": len(stories),
    }


@router.get(
    "/{story_id}",
    response_model=StoryRead,
    status_code=status.HTTP_200_OK,
)
async def get_story(
    story_id: UUID,
    owner_id: UUID | None = None,
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> StoryRead:
    """Retrieve one of the authenticated user's stories."""

    story = await story_service.get_story(
        conn,
        story_id,
        ensure_self(owner_id, profile, "owner_id"),
    )

    if story is None:
        raise NotFoundError("Story not found.")

    return story


@router.delete(
    "/{story_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_story(
    story_id: UUID,
    owner_id: UUID | None = None,
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> Response:
    """Soft-delete one of the authenticated user's stories."""

    story = await story_service.delete_story(
        conn,
        story_id,
        ensure_self(owner_id, profile, "owner_id"),
    )

    if story is None:
        raise NotFoundError("Story not found.")

    return Response(status_code=status.HTTP_204_NO_CONTENT)
