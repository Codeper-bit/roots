
from uuid import UUID

import asyncpg

from app.repositories import consent_repository


async def create_consent(
    conn: asyncpg.Connection,
    *,
    participant_id: UUID,
    purpose: str,
    status: str,
) -> asyncpg.Record:
    """
    Record a participant's consent decision.

    A decision can initially be granted or declined.
    """

    return await consent_repository.create_consent_record(
        conn,
        participant_id=participant_id,
        purpose=purpose,
        status=status,
    )


async def get_consent(
    conn: asyncpg.Connection,
    consent_id: UUID,
) -> asyncpg.Record | None:
    """Retrieve one consent record."""

    return await consent_repository.get_consent_by_id(
        conn,
        consent_id,
    )


async def list_consents(
    conn: asyncpg.Connection,
    participant_id: UUID,
) -> list[asyncpg.Record]:
    """Retrieve the complete consent history of a participant."""

    return await consent_repository.list_participant_consents(
        conn,
        participant_id,
    )


async def get_active_consent(
    conn: asyncpg.Connection,
    participant_id: UUID,
    purpose: str,
) -> asyncpg.Record | None:
    """Retrieve an active grant for a particular purpose."""

    return await consent_repository.get_active_consent(
        conn,
        participant_id,
        purpose,
    )


async def has_active_consent(
    conn: asyncpg.Connection,
    participant_id: UUID,
    purpose: str,
) -> bool:
    """Check whether a participant has granted a particular permission."""

    consent = await get_active_consent(
        conn,
        participant_id,
        purpose,
    )

    return consent is not None


async def require_active_consent(
    conn: asyncpg.Connection,
    participant_id: UUID,
    purpose: str,
) -> asyncpg.Record:
    """
    Ensure the participant has granted the required permission.

    Raises PermissionError if permission is absent.
    """

    consent = await get_active_consent(
        conn,
        participant_id,
        purpose,
    )

    if consent is None:
        raise PermissionError(
            f"Participant has not granted consent for: {purpose}"
        )

    return consent


async def withdraw_consent(
    conn: asyncpg.Connection,
    consent_id: UUID,
) -> asyncpg.Record | None:
    """
    Withdraw an existing active consent grant.

    Returns None if the record does not exist or is not active.
    """

    return await consent_repository.withdraw_consent(
        conn,
        consent_id,
    )
