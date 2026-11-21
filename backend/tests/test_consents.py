
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_db_connection
from app.api.routes.consents import router
from app.services import consent_service


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
def consent_data():
    now = datetime.now(timezone.utc)

    return {
        "id": uuid4(),
        "participant_id": uuid4(),
        "purpose": "transcription",
        "status": "granted",
        "granted_at": now,
        "withdrawn_at": None,
        "created_at": now,
        "updated_at": now,
    }


def test_create_consent(client, consent_data, monkeypatch):
    mock_create = AsyncMock(return_value=consent_data)
    monkeypatch.setattr(
        consent_service, "create_consent", mock_create
    )

    response = client.post(
        "/consents",
        json={
            "participant_id": str(consent_data["participant_id"]),
            "purpose": "transcription",
            "status": "granted",
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(consent_data["id"])
    assert response.json()["status"] == "granted"
    mock_create.assert_awaited_once()


def test_create_consent_rejects_invalid_status(client, consent_data):
    response = client.post(
        "/consents",
        json={
            "participant_id": str(consent_data["participant_id"]),
            "purpose": "transcription",
            "status": "withdrawn",
        },
    )

    assert response.status_code == 422


def test_get_consent(client, consent_data, monkeypatch):
    mock_get = AsyncMock(return_value=consent_data)
    monkeypatch.setattr(consent_service, "get_consent", mock_get)

    response = client.get(f"/consents/{consent_data['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == str(consent_data["id"])
    mock_get.assert_awaited_once()


def test_get_consent_returns_404(client, monkeypatch):
    mock_get = AsyncMock(return_value=None)
    monkeypatch.setattr(consent_service, "get_consent", mock_get)

    response = client.get(f"/consents/{uuid4()}")

    assert response.status_code == 404


def test_list_consents(client, consent_data, monkeypatch):
    mock_list = AsyncMock(return_value=[consent_data])
    monkeypatch.setattr(
        consent_service, "list_consents", mock_list
    )

    response = client.get(
        f"/participants/{consent_data['participant_id']}/consents"
    )

    assert response.status_code == 200
    assert len(response.json()["consents"]) == 1
    assert response.json()["consents"][0]["id"] == str(
        consent_data["id"]
    )
    mock_list.assert_awaited_once()


def test_list_consents_returns_empty_list(client, monkeypatch):
    mock_list = AsyncMock(return_value=[])
    monkeypatch.setattr(
        consent_service, "list_consents", mock_list
    )

    response = client.get(
        f"/participants/{uuid4()}/consents"
    )

    assert response.status_code == 200
    assert response.json() == {"consents": []}


def test_get_active_consent(client, consent_data, monkeypatch):
    mock_active = AsyncMock(return_value=consent_data)
    monkeypatch.setattr(
        consent_service, "get_active_consent", mock_active
    )

    response = client.get(
        f"/participants/{consent_data['participant_id']}"
        "/consents/transcription/active"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "granted"
    mock_active.assert_awaited_once()


def test_get_active_consent_returns_404(client, monkeypatch):
    mock_active = AsyncMock(return_value=None)
    monkeypatch.setattr(
        consent_service, "get_active_consent", mock_active
    )

    response = client.get(
        f"/participants/{uuid4()}/consents/transcription/active"
    )

    assert response.status_code == 404


def test_get_active_consent_rejects_invalid_purpose(client):
    response = client.get(
        f"/participants/{uuid4()}/consents/invalid_purpose/active"
    )

    assert response.status_code == 422


def test_withdraw_consent(client, consent_data, monkeypatch):
    withdrawn = {
        **consent_data,
        "status": "withdrawn",
        "withdrawn_at": datetime.now(timezone.utc),
    }

    mock_withdraw = AsyncMock(return_value=withdrawn)
    monkeypatch.setattr(
        consent_service, "withdraw_consent", mock_withdraw
    )

    response = client.post(
        f"/consents/{consent_data['id']}/withdraw"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "withdrawn"
    assert response.json()["withdrawn_at"] is not None
    mock_withdraw.assert_awaited_once()


def test_withdraw_consent_returns_404_when_not_active(
    client, monkeypatch
):
    mock_withdraw = AsyncMock(return_value=None)
    monkeypatch.setattr(
        consent_service, "withdraw_consent", mock_withdraw
    )

    response = client.post(
        f"/consents/{uuid4()}/withdraw"
    )

    assert response.status_code == 404
