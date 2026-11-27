from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth_dependencies import get_current_profile
from app.api.authorization import ensure_self, require_content_version
from app.api.dependencies import get_db_connection
from app.core.errors import ForbiddenError, NotFoundError
from app.schemas.content import ContentReviewCreate, ContentReviewRead
from app.services import content_service

router = APIRouter(prefix="/content-reviews", tags=["content reviews"])


@router.post(
    "",
    response_model=ContentReviewRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_content_review(
    payload: ContentReviewCreate,
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ContentReviewRead:
    await require_content_version(conn, payload.content_version_id, profile)
    reviewer_id = ensure_self(payload.reviewer_id, profile, "reviewer_id")

    try:
        review = await content_service.review_content(
            conn,
            content_version_id=payload.content_version_id,
            reviewer_id=reviewer_id,
            decision=payload.decision,
            comment=payload.comment,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    if review is None:
        raise NotFoundError("Content version not found.")

    return review


@router.get(
    "/version/{content_version_id}",
    response_model=list[ContentReviewRead],
)
async def get_content_reviews(
    content_version_id: UUID,
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> list[ContentReviewRead]:
    await require_content_version(conn, content_version_id, profile)
    return await content_service.get_content_reviews(conn, content_version_id)


@router.get(
    "/reviewer/{reviewer_id}",
    response_model=list[ContentReviewRead],
)
async def get_reviewer_history(
    reviewer_id: UUID,
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> list[ContentReviewRead]:
    if reviewer_id != profile["id"]:
        raise ForbiddenError("You can only view your own review history.")
    return await content_service.get_reviewer_history(conn, reviewer_id)
