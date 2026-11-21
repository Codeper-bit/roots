from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_db_connection
from app.api.routes.participants import router
from app.services import participant_service


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
def participant_data():
    now = datetime.now(timezone.utc)

    return {
        "id": uuid4(),
        "story_id": uuid4(),
        "user_id": None,
        "display_name": "Grandfather",
        "role": "storyteller",
        "created_at": now,
        "updated_at": now,
    }


def test_create_participant(client, participant_data, monkeypatch):
    mock_create = AsyncMock(return_value=participant_data)
    monkeypatch.setattr(
        participant_service, "create_participant", mock_create
    )

    response = client.post(
        "/participants",
        json={
            "story_id": str(participant_data["story_id"]),
            "display_name": "Grandfather",
            "role": "storyteller",
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(participant_data["id"])
    assert response.json()["display_name"] == "Grandfather"
    mock_create.assert_awaited_once()


def test_create_participant_rejects_blank_name(client, participant_data):
    response = client.post(
        "/participants",
        json={
            "story_id": str(participant_data["story_id"]),
            "display_name": "   ",
            "role": "storyteller",
        },
    )

    assert response.status_code == 422


def test_get_participant(client, participant_data, monkeypatch):
    mock_get = AsyncMock(return_value=participant_data)
    monkeypatch.setattr(
        participant_service, "get_participant", mock_get
    )

    response = client.get(
        f"/participants/{participant_data['id']}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(participant_data["id"])
    mock_get.assert_awaited_once()


def test_get_participant_returns_404(client, monkeypatch):
    mock_get = AsyncMock(return_value=None)
    monkeypatch.setattr(
        participant_service, "get_participant", mock_get
    )

    response = client.get(f"/participants/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found."


def test_list_participants(client, participant_data, monkeypatch):
    mock_list = AsyncMock(return_value=[participant_data])
    monkeypatch.setattr(
        participant_service, "list_participants", mock_list
    )

    response = client.get(
        f"/stories/{participant_data['story_id']}/participants"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == str(participant_data["id"])
    mock_list.assert_awaited_once()


def test_list_participants_returns_empty_list(client, monkeypatch):
    mock_list = AsyncMock(return_value=[])
    monkeypatch.setattr(
        participant_service, "list_participants", mock_list
    )

    response = client.get(
        f"/stories/{uuid4()}/participants"
    )

    assert response.status_code == 200
    assert response.json() == []


def test_update_participant(client, participant_data, monkeypatch):
    updated = {
        **participant_data,
        "display_name": "Updated Grandfather",
    }

    mock_update = AsyncMock(return_value=updated)
    monkeypatch.setattr(
        participant_service, "update_participant", mock_update
    )

    response = client.patch(
        f"/stories/{participant_data['story_id']}/participants/"
        f"{participant_data['id']}",
        json={"display_name": "Updated Grandfather"},
    )

    assert response.status_code == 200
    assert response.json()["display_name"] == "Updated Grandfather"
    mock_update.assert_awaited_once()


def test_update_participant_returns_404(client, monkeypatch):
    mock_update = AsyncMock(return_value=None)
    monkeypatch.setattr(
        participant_service, "update_participant", mock_update
    )

    response = client.patch(
        f"/stories/{uuid4()}/participants/{uuid4()}",
        json={"role": "interviewer"},
    )

    assert response.status_code == 404


def test_update_participant_rejects_empty_payload(client):
    response = client.patch(
        f"/stories/{uuid4()}/participants/{uuid4()}",
        json={},
    )

    assert response.status_code == 422
