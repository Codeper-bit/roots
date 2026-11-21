from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_db_connection
from app.api.routes.stories import router
from app.services import story_service


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)

    async def override_db_connection():
        yield object()

    app.dependency_overrides[get_db_connection] = override_db_connection

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def story_data():
    now = datetime.now(timezone.utc)

    return {
        "id": uuid4(),
        "owner_id": uuid4(),
        "title": "My Grandfather's Story",
        "description": "A story about family history.",
        "source_language": "yor",
        "status": "draft",
        "visibility": "private",
        "deleted_at": None,
        "created_at": now,
        "updated_at": now,
    }


def test_create_story(client, story_data, monkeypatch):
    mock_create = AsyncMock(return_value=story_data)
    monkeypatch.setattr(
        story_service,
        "create_story",
        mock_create,
    )

    response = client.post(
        "/stories",
        json={
            "owner_id": str(story_data["owner_id"]),
            "title": "My Grandfather's Story",
            "description": "A story about family history.",
            "source_language": "yor",
            "visibility": "private",
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(story_data["id"])
    assert response.json()["title"] == "My Grandfather's Story"

    mock_create.assert_awaited_once()


def test_create_story_rejects_invalid_data(client):
    response = client.post(
        "/stories",
        json={
            "owner_id": str(uuid4()),
            "title": "   ",
            "source_language": "yor",
            "visibility": "private",
        },
    )

    assert response.status_code == 422


def test_list_stories(client, story_data, monkeypatch):
    stories = [story_data]

    mock_list = AsyncMock(return_value=stories)
    monkeypatch.setattr(
        story_service,
        "list_stories",
        mock_list,
    )

    response = client.get(
        "/stories",
        params={"owner_id": str(story_data["owner_id"])},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["stories"]) == 1
    assert response.json()["stories"][0]["id"] == str(story_data["id"])

    mock_list.assert_awaited_once_with(
        mock_list.await_args.args[0],
        story_data["owner_id"],
    )


def test_list_stories_returns_empty_list(client, monkeypatch):
    mock_list = AsyncMock(return_value=[])
    monkeypatch.setattr(
        story_service,
        "list_stories",
        mock_list,
    )

    response = client.get(
        "/stories",
        params={"owner_id": str(uuid4())},
    )

    assert response.status_code == 200
    assert response.json() == {
        "stories": [],
        "total": 0,
    }


def test_get_story(client, story_data, monkeypatch):
    mock_get = AsyncMock(return_value=story_data)
    monkeypatch.setattr(
        story_service,
        "get_story",
        mock_get,
    )

    response = client.get(
        f"/stories/{story_data['id']}",
        params={"owner_id": str(story_data["owner_id"])},
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(story_data["id"])
    assert response.json()["title"] == story_data["title"]

    mock_get.assert_awaited_once_with(
        mock_get.await_args.args[0],
        story_data["id"],
        story_data["owner_id"],
    )


def test_get_story_returns_404_when_not_found(client, monkeypatch):
    mock_get = AsyncMock(return_value=None)
    monkeypatch.setattr(
        story_service,
        "get_story",
        mock_get,
    )

    response = client.get(
        f"/stories/{uuid4()}",
        params={"owner_id": str(uuid4())},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Story not found."


def test_delete_story(client, story_data, monkeypatch):
    mock_delete = AsyncMock(return_value=story_data)
    monkeypatch.setattr(
        story_service,
        "delete_story",
        mock_delete,
    )

    response = client.delete(
        f"/stories/{story_data['id']}",
        params={"owner_id": str(story_data["owner_id"])},
    )

    assert response.status_code == 204
    assert response.content == b""

    mock_delete.assert_awaited_once_with(
        mock_delete.await_args.args[0],
        story_data["id"],
        story_data["owner_id"],
    )


def test_delete_story_returns_404_when_not_found(client, monkeypatch):
    mock_delete = AsyncMock(return_value=None)
    monkeypatch.setattr(
        story_service,
        "delete_story",
        mock_delete,
    )

    response = client.delete(
        f"/stories/{uuid4()}",
        params={"owner_id": str(uuid4())},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Story not found."
