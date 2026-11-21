
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_db_connection
from app.api.routes.reviews import router
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
def review_data():
    return {
        "id": uuid4(),
        "content_version_id": uuid4(),
        "reviewer_id": uuid4(),
        "decision": "approved",
        "comment": "Looks good.",
        "created_at": datetime.now(timezone.utc),
    }


def test_create_content_review(client, review_data, monkeypatch):
    mock_review = AsyncMock(return_value=review_data)

    monkeypatch.setattr(
        content_service,
        "review_content",
        mock_review,
    )

    response = client.post(
        "/content-reviews",
        json={
            "content_version_id": str(
                review_data["content_version_id"]
            ),
            "reviewer_id": str(review_data["reviewer_id"]),
            "decision": "approved",
            "comment": "Looks good.",
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(review_data["id"])
    assert response.json()["decision"] == "approved"
    assert response.json()["comment"] == "Looks good."

    mock_review.assert_awaited_once()


def test_create_content_review_rejects_invalid_decision(client):
    response = client.post(
        "/content-reviews",
        json={
            "content_version_id": str(uuid4()),
            "reviewer_id": str(uuid4()),
            "decision": "pending",
        },
    )

    assert response.status_code == 422


def test_create_content_review_returns_422_for_service_error(
    client, monkeypatch
):
    mock_review = AsyncMock(
        side_effect=ValueError("Invalid review decision.")
    )

    monkeypatch.setattr(
        content_service,
        "review_content",
        mock_review,
    )

    response = client.post(
        "/content-reviews",
        json={
            "content_version_id": str(uuid4()),
            "reviewer_id": str(uuid4()),
            "decision": "approved",
        },
    )

    assert response.status_code == 422


def test_create_content_review_returns_404_for_missing_version(
    client, monkeypatch
):
    mock_review = AsyncMock(return_value=None)

    monkeypatch.setattr(
        content_service,
        "review_content",
        mock_review,
    )

    response = client.post(
        "/content-reviews",
        json={
            "content_version_id": str(uuid4()),
            "reviewer_id": str(uuid4()),
            "decision": "approved",
        },
    )

    assert response.status_code == 404


def test_get_content_reviews(client, review_data, monkeypatch):
    mock_get = AsyncMock(return_value=[review_data])

    monkeypatch.setattr(
        content_service,
        "get_content_reviews",
        mock_get,
    )

    response = client.get(
        f"/content-reviews/version/{review_data['content_version_id']}"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["decision"] == "approved"

    mock_get.assert_awaited_once()


def test_get_content_reviews_empty(client, monkeypatch):
    mock_get = AsyncMock(return_value=[])

    monkeypatch.setattr(
        content_service,
        "get_content_reviews",
        mock_get,
    )

    response = client.get(
        f"/content-reviews/version/{uuid4()}"
    )

    assert response.status_code == 200
    assert response.json() == []


def test_get_reviewer_history(client, review_data, monkeypatch):
    mock_get = AsyncMock(return_value=[review_data])

    monkeypatch.setattr(
        content_service,
        "get_reviewer_history",
        mock_get,
    )

    response = client.get(
        f"/content-reviews/reviewer/{review_data['reviewer_id']}"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["reviewer_id"] == str(
        review_data["reviewer_id"]
    )

    mock_get.assert_awaited_once()


def test_get_reviewer_history_empty(client, monkeypatch):
    mock_get = AsyncMock(return_value=[])

    monkeypatch.setattr(
        content_service,
        "get_reviewer_history",
        mock_get,
    )

    response = client.get(
        f"/content-reviews/reviewer/{uuid4()}"
    )

    assert response.status_code == 200
    assert response.json() == []
