from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, status

from app.api.auth_dependencies import get_current_profile
from app.api.authorization import require_consent, require_participant
from app.api.dependencies import get_db_connection
from app.core.errors import NotFoundError
from app.schemas.common import ConsentPurpose
from app.schemas.consent import ConsentCreate, ConsentList, ConsentRead
from app.services import consent_service

router = APIRouter(tags=["consents"])


@router.post(
    "/consents",
    response_model=ConsentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_consent(
    payload: ConsentCreate,
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ConsentRead:
    await require_participant(conn, payload.participant_id, profile)

    return await consent_service.create_consent(
        conn,
        participant_id=payload.participant_id,
        purpose=payload.purpose,
        status=payload.status,
    )


@router.get(
    "/consents/{consent_id}",
    response_model=ConsentRead,
)
async def get_consent(
    consent_id: UUID,
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ConsentRead:
    return await require_consent(conn, consent_id, profile)


@router.get(
    "/participants/{participant_id}/consents",
    response_model=ConsentList,
)
async def list_consents(
    participant_id: UUID,
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ConsentList:
    await require_participant(conn, participant_id, profile)
    consents = await consent_service.list_consents(conn, participant_id)
    return {"consents": consents}


@router.get(
    "/participants/{participant_id}/consents/{purpose}/active",
    response_model=ConsentRead,
)
async def get_active_consent(
    participant_id: UUID,
    purpose: ConsentPurpose,
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ConsentRead:
    await require_participant(conn, participant_id, profile)

    consent = await consent_service.get_active_consent(
        conn, participant_id, purpose
    )

    if consent is None:
        raise NotFoundError("No active consent found for this purpose.")

    return consent


@router.post(
    "/consents/{consent_id}/withdraw",
    response_model=ConsentRead,
)
async def withdraw_consent(
    consent_id: UUID,
    profile: asyncpg.Record = Depends(get_current_profile),
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ConsentRead:
    await require_consent(conn, consent_id, profile)

    consent = await consent_service.withdraw_consent(conn, consent_id)

    if consent is None:
        raise NotFoundError("Active consent record not found.")

    return consent
