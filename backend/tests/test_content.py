
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_db_connection
from app.api.routes.content import router
from app.services import content_service


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
def content_data():
    now = datetime.now(timezone.utc)

    return {
        "id": uuid4(),
        "story_id": uuid4(),
        "content_type": "transcript",
        "language_code": "yo",
        "version_number": 1,
        "content": "Bawo ni gbogbo eniyan.",
        "origin": "ai_generated",
        "based_on_version_id": None,
        "created_by": None,
        "review_status": "unreviewed",
        "created_at": now,
        "updated_at": now,
    }


def test_create_content_version(client, content_data, monkeypatch):
    mock_create = AsyncMock(return_value=content_data)

    monkeypatch.setattr(
        content_service,
        "create_content_version",
        mock_create,
    )

    response = client.post(
        "/content-versions",
        json={
            "story_id": str(content_data["story_id"]),
            "content_type": "transcript",
            "language_code": "yo",
            "content": "Bawo ni gbogbo eniyan.",
            "origin": "ai_generated",
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(content_data["id"])
    assert response.json()["content_type"] == "transcript"
    assert response.json()["review_status"] == "unreviewed"

    mock_create.assert_awaited_once()


def test_create_content_version_rejects_invalid_content_type(client):
    response = client.post(
        "/content-versions",
        json={
            "story_id": str(uuid4()),
            "content_type": "audio",
            "language_code": "yo",
            "content": "Some content",
            "origin": "ai_generated",
        },
    )

    assert response.status_code == 422


def test_create_content_version_rejects_blank_content(client):
    response = client.post(
        "/content-versions",
        json={
            "story_id": str(uuid4()),
            "content_type": "transcript",
            "language_code": "yo",
            "content": "   ",
            "origin": "ai_generated",
        },
    )

    assert response.status_code == 422


def test_create_content_version_requires_creator_for_human_content(client):
    response = client.post(
        "/content-versions",
        json={
            "story_id": str(uuid4()),
            "content_type": "transcript",
            "language_code": "yo",
            "content": "Human-created transcript.",
            "origin": "human_created",
        },
    )

    assert response.status_code == 422


def test_create_content_version_requires_base_for_human_edit(client):
    response = client.post(
        "/content-versions",
        json={
            "story_id": str(uuid4()),
            "content_type": "transcript",
            "language_code": "yo",
            "content": "Edited transcript.",
            "origin": "human_edited",
            "created_by": str(uuid4()),
        },
    )

    assert response.status_code == 422


def test_create_content_version_returns_422_for_service_error(
    client, monkeypatch
):
    mock_create = AsyncMock(
        side_effect=ValueError("Invalid content type.")
    )

    monkeypatch.setattr(
        content_service,
        "create_content_version",
        mock_create,
    )

    response = client.post(
        "/content-versions",
        json={
            "story_id": str(uuid4()),
            "content_type": "transcript",
            "language_code": "yo",
            "content": "Some content",
            "origin": "ai_generated",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid content type."


def test_get_content_version(client, content_data, monkeypatch):
    mock_get = AsyncMock(return_value=content_data)

    monkeypatch.setattr(
        content_service,
        "get_content_version",
        mock_get,
    )

    response = client.get(
        f"/content-versions/{content_data['id']}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(content_data["id"])
    assert response.json()["content"] == "Bawo ni gbogbo eniyan."

    mock_get.assert_awaited_once()


def test_get_content_version_returns_404(client, monkeypatch):
    mock_get = AsyncMock(return_value=None)

    monkeypatch.setattr(
        content_service,
        "get_content_version",
        mock_get,
    )

    response = client.get(
        f"/content-versions/{uuid4()}"
    )

    assert response.status_code == 404


def test_get_story_content_versions(
    client, content_data, monkeypatch
):
    second_version = {
        **content_data,
        "id": uuid4(),
        "version_number": 2,
        "content": "Updated transcript.",
    }

    mock_get = AsyncMock(
        return_value=[content_data, second_version]
    )

    monkeypatch.setattr(
        content_service,
        "get_story_content_versions",
        mock_get,
    )

    response = client.get(
        f"/stories/{content_data['story_id']}/content-versions"
    )

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["version_number"] == 1
    assert response.json()[1]["version_number"] == 2

    mock_get.assert_awaited_once()


def test_get_story_content_versions_empty(client, monkeypatch):
    mock_get = AsyncMock(return_value=[])

    monkeypatch.setattr(
        content_service,
        "get_story_content_versions",
        mock_get,
    )

    response = client.get(
        f"/stories/{uuid4()}/content-versions"
    )

    assert response.status_code == 200
    assert response.json() == []


def test_get_latest_content(client, content_data, monkeypatch):
    mock_get = AsyncMock(return_value=content_data)

    monkeypatch.setattr(
        content_service,
        "get_latest_content",
        mock_get,
    )

    response = client.get(
        f"/stories/{content_data['story_id']}/content/latest",
        params={
            "content_type": "transcript",
            "language_code": "yo",
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(content_data["id"])

    mock_get.assert_awaited_once()


def test_get_latest_content_returns_404(client, monkeypatch):
    mock_get = AsyncMock(return_value=None)

    monkeypatch.setattr(
        content_service,
        "get_latest_content",
        mock_get,
    )

    response = client.get(
        f"/stories/{uuid4()}/content/latest",
        params={
            "content_type": "transcript",
            "language_code": "yo",
        },
    )

    assert response.status_code == 404


def test_get_latest_content_rejects_invalid_type(client, monkeypatch):
    mock_get = AsyncMock(
        side_effect=ValueError("Invalid content type.")
    )

    monkeypatch.setattr(
        content_service,
        "get_latest_content",
        mock_get,
    )

    response = client.get(
        f"/stories/{uuid4()}/content/latest",
        params={
            "content_type": "audio",
            "language_code": "yo",
        },
    )

    assert response.status_code == 422
