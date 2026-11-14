import asyncio
import os
from collections.abc import AsyncIterator
from pathlib import Path
from urllib.parse import urlparse

import asyncpg
import pytest

SCHEMA_FILE = Path(__file__).resolve().parent.parent / \
    "sql" / "001_initial.sql"


def _test_database_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.fail(
            "TEST_DATABASE_URL is not set. Point it at a dedicated test database, e.g. "
            "postgresql://roots:change-me@localhost:5432/roots_test",
            pytrace=False,
        )
    database_name = urlparse(url).path.lstrip("/")
    if not database_name.endswith("_test"):
        # Safety net: the schema is wiped, so refuse to touch a database not named *_test.
        pytest.fail(
            f"Refusing to run: database name '{database_name}' does not end in '_test'.",
            pytrace=False,
        )
    return url


async def _rebuild_schema(url: str) -> None:
    connection = await asyncpg.connect(url)
    try:
        await connection.execute("DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;")
        await connection.execute(SCHEMA_FILE.read_text(encoding="utf-8"))
    finally:
        await connection.close()


@pytest.fixture(scope="session")
def database_url() -> str:
    url = _test_database_url()
    asyncio.run(_rebuild_schema(url))
    return url


@pytest.fixture
async def conn(database_url: str) -> AsyncIterator[asyncpg.Connection]:
    """A connection inside a transaction that is always rolled back."""
    connection = await asyncpg.connect(database_url)
    outer = connection.transaction()
    await outer.start()
    try:
        yield connection
    finally:
        await outer.rollback()
        await connection.close()
