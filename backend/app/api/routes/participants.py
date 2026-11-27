from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth_dependencies import get_current_profile
from app.api.authorization import require_participant, require_story
from app.api.dependencies import get_db_connection
from app.core.errors import NotFoundError
from app.schemas.participant import (
    ParticipantCreate,
    ParticipantRead,
    ParticipantUpdate,
)
from app.services import participant_service

router = APIRouter(tags=["participants"])


@router.post(
    "/participants",
    response_model=ParticipantRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_participant(
    payload: ParticipantCreate,
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ParticipantRead:
    await require_story(conn, payload.story_id, profile)

    return await participant_service.create_participant(
        conn,
        story_id=payload.story_id,
        user_id=payload.user_id,
        display_name=payload.display_name,
        role=payload.role,
    )


@router.get(
    "/participants/{participant_id}",
    response_model=ParticipantRead,
)
async def get_participant(
    participant_id: UUID,
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ParticipantRead:
    return await require_participant(conn, participant_id, profile)


@router.get(
    "/stories/{story_id}/participants",
    response_model=list[ParticipantRead],
)
async def list_participants(
    story_id: UUID,
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> list[ParticipantRead]:
    await require_story(conn, story_id, profile)
    return await participant_service.list_participants(conn, story_id)


@router.patch(
    "/stories/{story_id}/participants/{participant_id}",
    response_model=ParticipantRead,
)
async def update_participant(
    story_id: UUID,
    participant_id: UUID,
    payload: ParticipantUpdate,
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ParticipantRead:
    if payload.display_name is None and payload.role is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide at least one field to update.",
        )

    await require_story(conn, story_id, profile)

    participant = await participant_service.update_participant(
        conn,
        participant_id,
        story_id,
        display_name=payload.display_name,
        role=payload.role,
    )

    if participant is None:
        raise NotFoundError("Participant not found.")

    return participant
