import asyncpg


async def is_language_available(conn: asyncpg.Connection, code: str) -> bool:
    """True when ``code`` exists in the languages table and is active."""
    return bool(
        await conn.fetchval(
            "SELECT is_active FROM languages WHERE code = $1",
            code,
        )
    )
