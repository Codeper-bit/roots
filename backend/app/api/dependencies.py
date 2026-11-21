
from collections.abc import AsyncIterator

import asyncpg
from fastapi import Request

from app.core.database import acquire


async def get_db_connection(
    request: Request,
) -> AsyncIterator[asyncpg.Connection]:
    """Provide a database connection for the duration of an API request."""
    pool: asyncpg.Pool = request.app.state.db_pool

    async with acquire(pool) as connection:
        yield connection
