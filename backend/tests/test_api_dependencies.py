
from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest

from app.api.dependencies import get_db_connection


@pytest.mark.asyncio
async def test_get_db_connection_yields_and_releases_connection():
    connection = object()
    state = {"acquired": False, "released": False}

    @asynccontextmanager
    async def mock_acquire():
        state["acquired"] = True
        try:
            yield connection
        finally:
            state["released"] = True

    pool = SimpleNamespace(acquire=mock_acquire)

    request = SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(db_pool=pool)
        )
    )

    dependency = get_db_connection(request)

    result = await anext(dependency)

    assert result is connection
    assert state["acquired"] is True
    assert state["released"] is False

    await dependency.aclose()

    assert state["released"] is True
