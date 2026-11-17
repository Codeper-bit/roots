
from uuid import UUID

import asyncpg


VALID_PURPOSES = {
    "audio_storage",
    "transcription",
    "translation",
    "cultural_interpretation",
    "family_sharing",
}

INITIAL_STATUSES = {"granted", "declined"}


async def create_consent_record(
    conn: asyncpg.Connection,
    *,
    participant_id: UUID,
    purpose: str,
    status: str,
) -> asyncpg.Record:
    if purpose not in VALID_PURPOSES:
        raise ValueError("Invalid consent purpose")

    if status not in INITIAL_STATUSES:
        raise ValueError("Consent must initially be granted or declined")

    query = """
        INSERT INTO consent_records (
            participant_id,
            purpose,
            status,
            granted_at
        )
        VALUES (
            $1,
            $2,
            $3,
            CASE
                WHEN $3 = 'granted' THEN NOW()
                ELSE NULL
            END
        )
        RETURNING *
    """

    return await conn.fetchrow(
        query,
        participant_id,
        purpose,
        status,
    )


async def get_consent_by_id(
    conn: asyncpg.Connection,
    consent_id: UUID,
) -> asyncpg.Record | None:
    query = """
        SELECT *
        FROM consent_records
        WHERE id = $1
    """

    return await conn.fetchrow(query, consent_id)


async def list_participant_consents(
    conn: asyncpg.Connection,
    participant_id: UUID,
) -> list[asyncpg.Record]:
    query = """
        SELECT *
        FROM consent_records
        WHERE participant_id = $1
        ORDER BY created_at ASC, id ASC
    """

    return await conn.fetch(query, participant_id)
