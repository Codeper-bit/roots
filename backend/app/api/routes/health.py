import asyncio

import asyncpg
from fastapi import APIRouter, HTTPException, Request, status

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(request: Request) -> dict[str, str]:
    """Report API availability and verify that PostgreSQL can answer a query."""
    pool: asyncpg.Pool = request.app.state.db_pool

    try:
        async with pool.acquire() as connection:
            await connection.fetchval("SELECT 1")
    except (asyncpg.PostgresError, asyncpg.InterfaceError, OSError, asyncio.TimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unhealthy", "database": "unavailable"},
        ) from exc

    return {"status": "healthy", "database": "connected"}
