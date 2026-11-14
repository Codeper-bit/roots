import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import asyncpg

from app.core.config import Settings

logger = logging.getLogger(__name__)


class DatabaseConnectionError(RuntimeError):
    """Raised when the connection pool cannot be created."""


async def create_pool(settings: Settings) -> asyncpg.Pool:
    """Open a connection pool. Called once, at application startup."""
    try:
        pool = await asyncpg.create_pool(
            dsn=settings.database_url.get_secret_value(),
            min_size=settings.db_pool_min_size,
            max_size=settings.db_pool_max_size,
            command_timeout=settings.db_command_timeout,
            server_settings={"application_name": "roots-api"},
        )
    except (OSError, asyncpg.PostgresError, asyncpg.InterfaceError) as exc:
        # Deliberately generic: never echo the connection string (it contains the password).
        raise DatabaseConnectionError(
            "Could not connect to PostgreSQL. Check DATABASE_URL and that the server is running."
        ) from exc
    logger.info("Database pool created (min=%s, max=%s)",
                settings.db_pool_min_size, settings.db_pool_max_size)
    return pool


async def close_pool(pool: asyncpg.Pool) -> None:
    """Wait for borrowed connections to be returned, then close everything."""
    await pool.close()
    logger.info("Database pool closed")


@asynccontextmanager
async def acquire(pool: asyncpg.Pool) -> AsyncIterator[asyncpg.Connection]:
    """Borrow a connection for a single operation; it is returned to the pool automatically."""
    async with pool.acquire() as connection:
        yield connection


@asynccontextmanager
async def transaction(pool: asyncpg.Pool) -> AsyncIterator[asyncpg.Connection]:
    """Borrow a connection and run everything inside it as one transaction.

    Commits if the block finishes normally. Rolls back if it raises.
    """
    async with pool.acquire() as connection:
        async with connection.transaction():
            yield connection
