from contextlib import asynccontextmanager

from fastapi.testclient import TestClient

from app.main import create_app


class FakeConnection:
    async def fetchval(self, query: str) -> int:
        assert query == "SELECT 1"
        return 1


class FakePool:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    @asynccontextmanager
    async def acquire(self):
        if self.fail:
            raise OSError("database unavailable")
        yield FakeConnection()


class FakeSettings:
    pass


def make_client(monkeypatch, pool: FakePool) -> TestClient:
    import app.main as main_module

    async def fake_create_pool(settings):
        return pool

    async def fake_close_pool(received_pool):
        assert received_pool is pool

    monkeypatch.setattr(main_module, "get_settings", lambda: FakeSettings())
    monkeypatch.setattr(main_module, "create_pool", fake_create_pool)
    monkeypatch.setattr(main_module, "close_pool", fake_close_pool)

    return TestClient(create_app())


def test_health_returns_healthy_when_database_query_succeeds(monkeypatch):
    with make_client(monkeypatch, FakePool()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "database": "connected"}


def test_health_returns_503_when_database_is_unavailable(monkeypatch):
    with make_client(monkeypatch, FakePool(fail=True)) as client:
        response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {
        "detail": {"status": "unhealthy", "database": "unavailable"}
    }
