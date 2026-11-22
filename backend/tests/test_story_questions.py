
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_db_connection
from app.api.routes.story_questions import router
from app.services import story_question_service


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
def question_data():
    now = datetime.now(timezone.utc)
    return {
        "id": uuid4(),
        "story_id": uuid4(),
        "question": "What was your childhood like?",
        "status": "suggested",
        "created_at": now,
        "updated_at": now,
    }


def test_create_question(client, question_data, monkeypatch):
    mock = AsyncMock(return_value=question_data)
    monkeypatch.setattr(
        story_question_service,
        "create_story_question",
        mock,
    )

    response = client.post(
        "/story-questions",
        json={
            "story_id": str(question_data["story_id"]),
            "question": question_data["question"],
        },
    )

    assert response.status_code == 201
    assert response.json()["question"] == question_data["question"]
    mock.assert_awaited_once()


def test_create_question_rejects_blank_question(client):
    response = client.post(
        "/story-questions",
        json={
            "story_id": str(uuid4()),
            "question": "   ",
        },
    )

    assert response.status_code == 422


def test_get_question(client, question_data, monkeypatch):
    mock = AsyncMock(return_value=question_data)
    monkeypatch.setattr(
        story_question_service,
        "get_story_question",
        mock,
    )

    response = client.get(
        f"/story-questions/{question_data['id']}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(question_data["id"])
    mock.assert_awaited_once()


def test_get_missing_question_returns_404(client, monkeypatch):
    mock = AsyncMock(return_value=None)
    monkeypatch.setattr(
        story_question_service,
        "get_story_question",
        mock,
    )

    response = client.get(f"/story-questions/{uuid4()}")

    assert response.status_code == 404


def test_list_story_questions(client, question_data, monkeypatch):
    mock = AsyncMock(return_value=[question_data])
    monkeypatch.setattr(
        story_question_service,
        "get_story_questions",
        mock,
    )

    response = client.get(
        f"/stories/{question_data['story_id']}/questions"
    )

    assert response.status_code == 200
    assert len(response.json()["questions"]) == 1
    mock.assert_awaited_once()


def test_update_question_status(client, question_data, monkeypatch):
    updated = {**question_data, "status": "asked"}
    mock = AsyncMock(return_value=updated)
    monkeypatch.setattr(
        story_question_service,
        "update_story_question_status",
        mock,
    )

    response = client.patch(
        f"/story-questions/{question_data['id']}/status",
        json={"status": "asked"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "asked"
    mock.assert_awaited_once()


def test_update_missing_question_returns_404(client, monkeypatch):
    mock = AsyncMock(return_value=None)
    monkeypatch.setattr(
        story_question_service,
        "update_story_question_status",
        mock,
    )

    response = client.patch(
        f"/story-questions/{uuid4()}/status",
        json={"status": "asked"},
    )

    assert response.status_code == 404


def test_update_question_rejects_invalid_status(client):
    response = client.patch(
        f"/story-questions/{uuid4()}/status",
        json={"status": "invalid"},
    )

    assert response.status_code == 422
