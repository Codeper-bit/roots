from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.dependencies import get_db_connection
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
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> StoryRead:
    """Create a new story."""

    story = await story_service.create_story(
        conn,
        owner_id=payload.owner_id,
        title=payload.title,
        source_language=payload.source_language,
        description=payload.description,
        visibility=payload.visibility,
    )

    return story


@router.get(
    "",
    response_model=StoryList,
    status_code=status.HTTP_200_OK,
)
async def list_stories(
    owner_id: UUID,
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> StoryList:
    """List all non-deleted stories belonging to a user."""

    stories = await story_service.list_stories(
        conn,
        owner_id,
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
    owner_id: UUID,
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> StoryRead:
    """Retrieve a story belonging to a user."""

    story = await story_service.get_story(
        conn,
        story_id,
        owner_id,
    )

    if story is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story not found.",
        )

    return story


@router.delete(
    "/{story_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_story(
    story_id: UUID,
    owner_id: UUID,
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> Response:
    """Soft-delete a story belonging to a user."""

    story = await story_service.delete_story(
        conn,
        story_id,
        owner_id,
    )

    if story is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story not found.",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
