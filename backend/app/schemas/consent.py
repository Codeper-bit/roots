
from datetime import datetime
from uuid import UUID

from pydantic import model_validator

from app.schemas.common import (
    ConsentDecision,
    ConsentPurpose,
    ConsentStatus,
    Schema,
    TimestampedSchema,
)


class ConsentCreate(Schema):
    participant_id: UUID
    purpose: ConsentPurpose
    status: ConsentDecision


class ConsentRead(TimestampedSchema):
    participant_id: UUID
    purpose: ConsentPurpose
    status: ConsentStatus
    granted_at: datetime | None
    withdrawn_at: datetime | None


class ConsentWithdrawal(Schema):
    consent_id: UUID


class ConsentList(Schema):
    consents: list[ConsentRead]
