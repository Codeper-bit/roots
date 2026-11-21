
import asyncpg
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_db_connection
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
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ParticipantRead:
    participant = await participant_service.create_participant(
        conn,
        story_id=payload.story_id,
        user_id=payload.user_id,
        display_name=payload.display_name,
        role=payload.role,
    )
    return participant


@router.get(
    "/participants/{participant_id}",
    response_model=ParticipantRead,
)
async def get_participant(
    participant_id: UUID,
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ParticipantRead:
    participant = await participant_service.get_participant(
        conn, participant_id
    )

    if participant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found.",
        )

    return participant


@router.get(
    "/stories/{story_id}/participants",
    response_model=list[ParticipantRead],
)
async def list_participants(
    story_id: UUID,
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> list[ParticipantRead]:
    return await participant_service.list_participants(conn, story_id)


@router.patch(
    "/stories/{story_id}/participants/{participant_id}",
    response_model=ParticipantRead,
)
async def update_participant(
    story_id: UUID,
    participant_id: UUID,
    payload: ParticipantUpdate,
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ParticipantRead:
    if payload.display_name is None and payload.role is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide at least one field to update.",
        )

    participant = await participant_service.update_participant(
        conn,
        participant_id,
        story_id,
        display_name=payload.display_name,
        role=payload.role,
    )

    if participant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found.",
        )

    return participant
