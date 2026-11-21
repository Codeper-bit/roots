from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_db_connection
from app.api.routes.audio import router
from app.services import audio_service


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
def audio_data():
    now = datetime.now(timezone.utc)

    return {
        "id": uuid4(),
        "story_id": uuid4(),
        "storage_key": "stories/example/audio-001.mp3",
        "mime_type": "audio/mpeg",
        "size_bytes": None,
        "duration_ms": None,
        "checksum": None,
        "upload_status": "pending",
        "created_at": now,
        "updated_at": now,
    }


def test_create_audio_asset(client, audio_data, monkeypatch):
    mock_create = AsyncMock(return_value=audio_data)
    monkeypatch.setattr(
        audio_service, "create_audio_asset", mock_create
    )

    response = client.post(
        "/audio-assets",
        json={
            "story_id": str(audio_data["story_id"]),
            "participant_id": str(uuid4()),
            "storage_key": audio_data["storage_key"],
            "mime_type": "audio/mpeg",
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(audio_data["id"])
    assert response.json()["upload_status"] == "pending"
    mock_create.assert_awaited_once()


def test_create_audio_asset_requires_consent(client, monkeypatch):
    mock_create = AsyncMock(
        side_effect=PermissionError(
            "Participant has not granted consent for: audio_storage"
        )
    )
    monkeypatch.setattr(
        audio_service, "create_audio_asset", mock_create
    )

    response = client.post(
        "/audio-assets",
        json={
            "story_id": str(uuid4()),
            "participant_id": str(uuid4()),
            "storage_key": "stories/example/audio.mp3",
            "mime_type": "audio/mpeg",
        },
    )

    assert response.status_code == 403
    assert "audio_storage" in response.json()["detail"]


def test_create_audio_asset_rejects_invalid_mime_type(client):
    response = client.post(
        "/audio-assets",
        json={
            "story_id": str(uuid4()),
            "participant_id": str(uuid4()),
            "storage_key": "stories/example/audio.mp3",
            "mime_type": "image/png",
        },
    )

    assert response.status_code == 422


def test_get_audio_asset(client, audio_data, monkeypatch):
    mock_get = AsyncMock(return_value=audio_data)
    monkeypatch.setattr(
        audio_service, "get_audio_asset", mock_get
    )

    response = client.get(
        f"/audio-assets/{audio_data['id']}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(audio_data["id"])
    mock_get.assert_awaited_once()


def test_get_audio_asset_returns_404(client, monkeypatch):
    mock_get = AsyncMock(return_value=None)
    monkeypatch.setattr(
        audio_service, "get_audio_asset", mock_get
    )

    response = client.get(f"/audio-assets/{uuid4()}")

    assert response.status_code == 404


def test_complete_audio_upload(client, audio_data, monkeypatch):
    uploaded = {
        **audio_data,
        "size_bytes": 500000,
        "duration_ms": 120000,
        "checksum": "a" * 64,
        "upload_status": "uploaded",
    }

    mock_complete = AsyncMock(return_value=uploaded)
    monkeypatch.setattr(
        audio_service, "mark_audio_uploaded", mock_complete
    )

    response = client.post(
        f"/audio-assets/{audio_data['id']}/complete",
        params={"participant_id": str(uuid4())},
        json={
            "size_bytes": 500000,
            "duration_ms": 120000,
            "checksum": "a" * 64,
        },
    )

    assert response.status_code == 200
    assert response.json()["upload_status"] == "uploaded"
    assert response.json()["size_bytes"] == 500000
    mock_complete.assert_awaited_once()


def test_complete_audio_upload_requires_consent(
    client, monkeypatch
):
    mock_complete = AsyncMock(
        side_effect=PermissionError(
            "Participant has not granted consent for: audio_storage"
        )
    )
    monkeypatch.setattr(
        audio_service, "mark_audio_uploaded", mock_complete
    )

    response = client.post(
        f"/audio-assets/{uuid4()}/complete",
        params={"participant_id": str(uuid4())},
        json={
            "size_bytes": 500000,
            "checksum": "a" * 64,
        },
    )

    assert response.status_code == 403


def test_complete_audio_upload_returns_404(
    client, monkeypatch
):
    mock_complete = AsyncMock(return_value=None)
    monkeypatch.setattr(
        audio_service, "mark_audio_uploaded", mock_complete
    )

    response = client.post(
        f"/audio-assets/{uuid4()}/complete",
        params={"participant_id": str(uuid4())},
        json={
            "size_bytes": 500000,
            "checksum": "a" * 64,
        },
    )

    assert response.status_code == 404


def test_complete_audio_upload_rejects_invalid_checksum(client):
    response = client.post(
        f"/audio-assets/{uuid4()}/complete",
        params={"participant_id": str(uuid4())},
        json={
            "size_bytes": 500000,
            "checksum": "invalid",
        },
    )

    assert response.status_code == 422


def test_fail_audio_upload(client, audio_data, monkeypatch):
    failed = {
        **audio_data,
        "upload_status": "failed",
    }

    mock_fail = AsyncMock(return_value=failed)
    monkeypatch.setattr(
        audio_service, "mark_audio_failed", mock_fail
    )

    response = client.post(
        f"/audio-assets/{audio_data['id']}/fail"
    )

    assert response.status_code == 200
    assert response.json()["upload_status"] == "failed"
    mock_fail.assert_awaited_once()


def test_fail_audio_upload_returns_404(client, monkeypatch):
    mock_fail = AsyncMock(return_value=None)
    monkeypatch.setattr(
        audio_service, "mark_audio_failed", mock_fail
    )

    response = client.post(
        f"/audio-assets/{uuid4()}/fail"
    )

    assert response.status_code == 404
