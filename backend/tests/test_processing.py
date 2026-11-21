
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_db_connection
from app.api.routes.processing import router
from app.services import processing_service


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
def job_data():
    now = datetime.now(timezone.utc)

    return {
        "id": uuid4(),
        "story_id": uuid4(),
        "audio_asset_id": uuid4(),
        "job_type": "transcription",
        "status": "queued",
        "attempts": 0,
        "error_message": None,
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
    }


def test_create_processing_job(client, job_data, monkeypatch):
    mock_create = AsyncMock(return_value=job_data)
    monkeypatch.setattr(
        processing_service, "create_processing_job", mock_create
    )

    response = client.post(
        "/processing-jobs",
        json={
            "story_id": str(job_data["story_id"]),
            "audio_asset_id": str(job_data["audio_asset_id"]),
            "job_type": "transcription",
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(job_data["id"])
    assert response.json()["status"] == "queued"
    mock_create.assert_awaited_once()


def test_create_processing_job_rejects_invalid_job_type(client, job_data):
    response = client.post(
        "/processing-jobs",
        json={
            "story_id": str(job_data["story_id"]),
            "job_type": "invalid_job",
        },
    )

    assert response.status_code == 422


def test_get_processing_job(client, job_data, monkeypatch):
    mock_get = AsyncMock(return_value=job_data)
    monkeypatch.setattr(
        processing_service, "get_processing_job", mock_get
    )

    response = client.get(
        f"/processing-jobs/{job_data['id']}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(job_data["id"])
    mock_get.assert_awaited_once()


def test_get_processing_job_returns_404(client, monkeypatch):
    mock_get = AsyncMock(return_value=None)
    monkeypatch.setattr(
        processing_service, "get_processing_job", mock_get
    )

    response = client.get(f"/processing-jobs/{uuid4()}")

    assert response.status_code == 404


def test_get_story_processing_jobs(client, job_data, monkeypatch):
    mock_list = AsyncMock(return_value=[job_data])
    monkeypatch.setattr(
        processing_service, "get_story_processing_jobs", mock_list
    )

    response = client.get(
        f"/processing-jobs/story/{job_data['story_id']}"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == str(job_data["id"])
    mock_list.assert_awaited_once()


def test_get_story_processing_jobs_returns_empty_list(
    client, monkeypatch
):
    mock_list = AsyncMock(return_value=[])
    monkeypatch.setattr(
        processing_service, "get_story_processing_jobs", mock_list
    )

    response = client.get(
        f"/processing-jobs/story/{uuid4()}"
    )

    assert response.status_code == 200
    assert response.json() == []


def test_update_processing_job_status(
    client, job_data, monkeypatch
):
    updated = {
        **job_data,
        "status": "running",
    }

    mock_update = AsyncMock(return_value=updated)
    monkeypatch.setattr(
        processing_service,
        "update_processing_job_status",
        mock_update,
    )

    response = client.patch(
        f"/processing-jobs/{job_data['id']}/status",
        json={"status": "running"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "running"
    mock_update.assert_awaited_once()


def test_update_processing_job_status_with_error(
    client, job_data, monkeypatch
):
    updated = {
        **job_data,
        "status": "failed",
        "error_message": "Transcription failed.",
    }

    mock_update = AsyncMock(return_value=updated)
    monkeypatch.setattr(
        processing_service,
        "update_processing_job_status",
        mock_update,
    )

    response = client.patch(
        f"/processing-jobs/{job_data['id']}/status",
        json={
            "status": "failed",
            "error_message": "Transcription failed.",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert response.json()["error_message"] == "Transcription failed."


def test_update_processing_job_status_returns_404(
    client, monkeypatch
):
    mock_update = AsyncMock(return_value=None)
    monkeypatch.setattr(
        processing_service,
        "update_processing_job_status",
        mock_update,
    )

    response = client.patch(
        f"/processing-jobs/{uuid4()}/status",
        json={"status": "running"},
    )

    assert response.status_code == 404


def test_update_processing_job_status_rejects_invalid_status(client):
    response = client.patch(
        f"/processing-jobs/{uuid4()}/status",
        json={"status": "unknown"},
    )

    assert response.status_code == 422
