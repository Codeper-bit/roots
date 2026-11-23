
from collections.abc import AsyncIterator

import asyncpg
from fastapi import Request
from supabase import Client

from app.core.database import acquire


async def get_db_connection(
    request: Request,
) -> AsyncIterator[asyncpg.Connection]:
    """Provide a database connection for the duration of an API request."""
    pool: asyncpg.Pool = request.app.state.db_pool

    async with acquire(pool) as connection:
        yield connection


def get_storage_client(request: Request) -> Client:
    """Provide the Supabase Storage client."""
    return request.app.state.storage_client


def get_storage_bucket(request: Request) -> str:
    return request.app.state.storage_bucket
