from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import Schema


class AuthProfileCreate(Schema):
    display_name: str = Field(min_length=1, max_length=100)


class AuthProfileRead(Schema):
    id: UUID
    supabase_auth_id: UUID
    email: str
    display_name: str
    created_at: datetime
    updated_at: datetime
