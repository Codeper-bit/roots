from app.repositories.consent_repository import (
    get_consent_by_id,
    list_participant_consents,
    create_consent_record,
    get_active_consent,
    withdraw_consent,
)
from uuid import uuid4

import asyncpg
import pytest
from tests import factories as f


async def create_participant(conn: asyncpg.Connection):
    owner = await f.insert_user(conn)
    story = await f.insert_story(conn, owner)
    return await f.insert_participant(conn, story)


async def test_create_granted_consent(conn: asyncpg.Connection) -> None:
    participant = await create_participant(conn)

    record = await create_consent_record(
        conn,
        participant_id=participant,
        purpose="transcription",
        status="granted",
    )

    assert record["participant_id"] == participant
    assert record["purpose"] == "transcription"
    assert record["status"] == "granted"
    assert record["granted_at"] is not None
    assert record["withdrawn_at"] is None


async def test_create_declined_consent(conn: asyncpg.Connection) -> None:
    participant = await create_participant(conn)

    record = await create_consent_record(
        conn,
        participant_id=participant,
        purpose="translation",
        status="declined",
    )

    assert record["status"] == "declined"
    assert record["granted_at"] is None
    assert record["withdrawn_at"] is None


async def test_invalid_purpose_is_rejected(conn: asyncpg.Connection) -> None:
    participant = await create_participant(conn)

    with pytest.raises(ValueError):
        await create_consent_record(
            conn,
            participant_id=participant,
            purpose="unknown_purpose",
            status="granted",
        )


async def test_withdrawn_cannot_be_created_directly(
    conn: asyncpg.Connection,
) -> None:
    participant = await create_participant(conn)

    with pytest.raises(ValueError):
        await create_consent_record(
            conn,
            participant_id=participant,
            purpose="transcription",
            status="withdrawn",
        )


async def test_nonexistent_participant_is_rejected(
    conn: asyncpg.Connection,
) -> None:
    with pytest.raises(asyncpg.ForeignKeyViolationError):
        async with conn.transaction():
            await create_consent_record(
                conn,
                participant_id=uuid4(),
                purpose="transcription",
                status="granted",
            )


async def test_only_one_active_grant_per_purpose(
    conn: asyncpg.Connection,
) -> None:
    participant = await create_participant(conn)

    await create_consent_record(
        conn,
        participant_id=participant,
        purpose="transcription",
        status="granted",
    )

    with pytest.raises(asyncpg.UniqueViolationError):
        async with conn.transaction():
            await create_consent_record(
                conn,
                participant_id=participant,
                purpose="transcription",
                status="granted",
            )


async def test_declined_consent_does_not_block_later_grant(
    conn: asyncpg.Connection,
) -> None:
    participant = await create_participant(conn)

    declined = await create_consent_record(
        conn,
        participant_id=participant,
        purpose="translation",
        status="declined",
    )

    granted = await create_consent_record(
        conn,
        participant_id=participant,
        purpose="translation",
        status="granted",
    )

    assert declined["status"] == "declined"
    assert granted["status"] == "granted"


async def test_get_consent_by_id(conn: asyncpg.Connection) -> None:
    participant = await create_participant(conn)

    created = await create_consent_record(
        conn,
        participant_id=participant,
        purpose="transcription",
        status="granted",
    )

    record = await get_consent_by_id(conn, created["id"])

    assert record is not None
    assert record["id"] == created["id"]


async def test_get_consent_by_id_returns_none_when_missing(
    conn: asyncpg.Connection,
) -> None:
    record = await get_consent_by_id(conn, uuid4())

    assert record is None


async def test_list_participant_consents(conn: asyncpg.Connection) -> None:
    participant = await create_participant(conn)

    await create_consent_record(
        conn,
        participant_id=participant,
        purpose="transcription",
        status="granted",
    )

    await create_consent_record(
        conn,
        participant_id=participant,
        purpose="translation",
        status="declined",
    )

    records = await list_participant_consents(conn, participant)

    assert len(records) == 2
    assert {record["purpose"] for record in records} == {
        "transcription",
        "translation",
    }


async def test_list_consents_does_not_return_other_participants_records(
    conn: asyncpg.Connection,
) -> None:
    participant_a = await create_participant(conn)
    participant_b = await create_participant(conn)

    await create_consent_record(
        conn,
        participant_id=participant_a,
        purpose="transcription",
        status="granted",
    )

    records = await list_participant_consents(conn, participant_b)

    assert records == []


async def test_get_active_consent(conn):
    participant = await create_participant(conn)

    created = await create_consent_record(
        conn,
        participant_id=participant,
        purpose="transcription",
        status="granted",
    )

    result = await get_active_consent(
        conn,
        participant,
        "transcription",
    )

    assert result is not None
    assert result["id"] == created["id"]


async def test_get_active_consent_returns_none_when_absent(conn):
    participant = await create_participant(conn)

    result = await get_active_consent(
        conn,
        participant,
        "transcription",
    )

    assert result is None


async def test_withdraw_consent(conn):
    participant = await create_participant(conn)

    created = await create_consent_record(
        conn,
        participant_id=participant,
        purpose="transcription",
        status="granted",
    )

    result = await withdraw_consent(conn, created["id"])

    assert result is not None
    assert result["status"] == "withdrawn"
    assert result["withdrawn_at"] is not None


async def test_cannot_withdraw_consent_twice(conn):
    participant = await create_participant(conn)

    created = await create_consent_record(
        conn,
        participant_id=participant,
        purpose="transcription",
        status="granted",
    )

    await withdraw_consent(conn, created["id"])

    result = await withdraw_consent(conn, created["id"])

    assert result is None
