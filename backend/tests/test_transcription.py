
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_db_connection
from app.api.routes.transcription import router
from app.services import transcription_service


@pytest.fixture
def app():
    application = FastAPI()
    application.include_router(router)

    async def override_db_connection():
        yield object()

    application.dependency_overrides[get_db_connection] = (
        override_db_connection
    )

    return application


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def transcription_data():
    now = datetime.now(timezone.utc)
    return {
        "id": uuid4(),
        "story_id": uuid4(),
        "content_type": "transcript",
        "language_code": "en",
        "version_number": 1,
        "content": "This is the transcribed story.",
        "origin": "ai_generated",
        "based_on_version_id": None,
        "created_by": None,
        "review_status": "unreviewed",
        "created_at": now,
        "updated_at": now,
    }


@pytest.fixture
def request_data():
    return {
        "participant_id": str(uuid4()),
        "story_id": str(uuid4()),
        "audio_asset_id": str(uuid4()),
        "language_code": "en",
    }


def test_transcribe_audio(
    app,
    client,
    request_data,
    transcription_data,
    monkeypatch,
):
    app.state.transcription_engine = AsyncMock(
        return_value="This is the transcribed story."
    )

    mock = AsyncMock(return_value=transcription_data)
    monkeypatch.setattr(
        transcription_service,
        "transcribe_audio",
        mock,
    )

    response = client.post(
        "/transcriptions",
        json=request_data,
    )

    assert response.status_code == 201
    assert response.json()["content"] == transcription_data["content"]
    mock.assert_awaited_once()


def test_transcription_provider_not_configured(
    client,
    request_data,
):
    response = client.post(
        "/transcriptions",
        json=request_data,
    )

    assert response.status_code == 503


def test_transcription_requires_valid_language_code(
    app,
    client,
    request_data,
):
    app.state.transcription_engine = AsyncMock()

    request_data["language_code"] = "english"

    response = client.post(
        "/transcriptions",
        json=request_data,
    )

    assert response.status_code == 422


def test_transcription_forbidden(
    app,
    client,
    request_data,
    monkeypatch,
):
    app.state.transcription_engine = AsyncMock()

    mock = AsyncMock(
        side_effect=PermissionError("Transcription consent is required.")
    )
    monkeypatch.setattr(
        transcription_service,
        "transcribe_audio",
        mock,
    )

    response = client.post(
        "/transcriptions",
        json=request_data,
    )

    assert response.status_code == 403


def test_transcription_invalid_audio(
    app,
    client,
    request_data,
    monkeypatch,
):
    app.state.transcription_engine = AsyncMock()

    mock = AsyncMock(
        side_effect=ValueError("Audio asset not found.")
    )
    monkeypatch.setattr(
        transcription_service,
        "transcribe_audio",
        mock,
    )

    response = client.post(
        "/transcriptions",
        json=request_data,
    )

    assert response.status_code == 422
