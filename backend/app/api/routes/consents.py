
import asyncpg
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_db_connection
from app.schemas.common import ConsentPurpose
from app.schemas.consent import ConsentCreate, ConsentRead, ConsentList
from app.services import consent_service

router = APIRouter(tags=["consents"])


@router.post(
    "/consents",
    response_model=ConsentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_consent(
    payload: ConsentCreate,
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ConsentRead:
    consent = await consent_service.create_consent(
        conn,
        participant_id=payload.participant_id,
        purpose=payload.purpose,
        status=payload.status,
    )
    return consent


@router.get(
    "/consents/{consent_id}",
    response_model=ConsentRead,
)
async def get_consent(
    consent_id: UUID,
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ConsentRead:
    consent = await consent_service.get_consent(conn, consent_id)

    if consent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consent record not found.",
        )

    return consent


@router.get(
    "/participants/{participant_id}/consents",
    response_model=ConsentList,
)
async def list_consents(
    participant_id: UUID,
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ConsentList:
    consents = await consent_service.list_consents(conn, participant_id)
    return {"consents": consents}


@router.get(
    "/participants/{participant_id}/consents/{purpose}/active",
    response_model=ConsentRead,
)
async def get_active_consent(
    participant_id: UUID,
    purpose: ConsentPurpose,
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ConsentRead:
    consent = await consent_service.get_active_consent(
        conn, participant_id, purpose
    )

    if consent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active consent found for this purpose.",
        )

    return consent


@router.post(
    "/consents/{consent_id}/withdraw",
    response_model=ConsentRead,
)
async def withdraw_consent(
    consent_id: UUID,
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> ConsentRead:
    consent = await consent_service.withdraw_consent(conn, consent_id)

    if consent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active consent record not found.",
        )

    return consent
