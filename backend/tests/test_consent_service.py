
import pytest
from unittest.mock import AsyncMock
from uuid import UUID

from app.repositories import consent_repository
from app.services import consent_service


@pytest.fixture
def conn():
    return object()


@pytest.mark.asyncio
async def test_create_consent(conn, monkeypatch):
    participant_id = UUID(int=1)

    expected = {
        "id": UUID(int=2),
        "participant_id": participant_id,
        "purpose": "transcription",
        "status": "granted",
    }

    mock_create = AsyncMock(return_value=expected)

    monkeypatch.setattr(
        consent_repository,
        "create_consent_record",
        mock_create,
    )

    result = await consent_service.create_consent(
        conn,
        participant_id=participant_id,
        purpose="transcription",
        status="granted",
    )

    assert result == expected

    mock_create.assert_awaited_once_with(
        conn,
        participant_id=participant_id,
        purpose="transcription",
        status="granted",
    )


@pytest.mark.asyncio
async def test_get_consent(conn, monkeypatch):
    consent_id = UUID(int=2)

    expected = {
        "id": consent_id,
        "purpose": "transcription",
        "status": "granted",
    }

    mock_get = AsyncMock(return_value=expected)

    monkeypatch.setattr(
        consent_repository,
        "get_consent_by_id",
        mock_get,
    )

    result = await consent_service.get_consent(
        conn,
        consent_id,
    )

    assert result == expected

    mock_get.assert_awaited_once_with(
        conn,
        consent_id,
    )


@pytest.mark.asyncio
async def test_get_consent_not_found(conn, monkeypatch):
    mock_get = AsyncMock(return_value=None)

    monkeypatch.setattr(
        consent_repository,
        "get_consent_by_id",
        mock_get,
    )

    result = await consent_service.get_consent(
        conn,
        UUID(int=2),
    )

    assert result is None


@pytest.mark.asyncio
async def test_list_consents(conn, monkeypatch):
    participant_id = UUID(int=1)

    expected = [
        {
            "purpose": "transcription",
            "status": "granted",
        },
        {
            "purpose": "translation",
            "status": "declined",
        },
    ]

    mock_list = AsyncMock(return_value=expected)

    monkeypatch.setattr(
        consent_repository,
        "list_participant_consents",
        mock_list,
    )

    result = await consent_service.list_consents(
        conn,
        participant_id,
    )

    assert result == expected
    assert len(result) == 2

    mock_list.assert_awaited_once_with(
        conn,
        participant_id,
    )


@pytest.mark.asyncio
async def test_get_active_consent(conn, monkeypatch):
    participant_id = UUID(int=1)

    expected = {
        "id": UUID(int=2),
        "participant_id": participant_id,
        "purpose": "transcription",
        "status": "granted",
    }

    mock_get = AsyncMock(return_value=expected)

    monkeypatch.setattr(
        consent_repository,
        "get_active_consent",
        mock_get,
    )

    result = await consent_service.get_active_consent(
        conn,
        participant_id,
        "transcription",
    )

    assert result == expected

    mock_get.assert_awaited_once_with(
        conn,
        participant_id,
        "transcription",
    )


@pytest.mark.asyncio
async def test_has_active_consent_true(conn, monkeypatch):
    mock_get = AsyncMock(
        return_value={"status": "granted"}
    )

    monkeypatch.setattr(
        consent_repository,
        "get_active_consent",
        mock_get,
    )

    result = await consent_service.has_active_consent(
        conn,
        UUID(int=1),
        "transcription",
    )

    assert result is True


@pytest.mark.asyncio
async def test_has_active_consent_false(conn, monkeypatch):
    mock_get = AsyncMock(return_value=None)

    monkeypatch.setattr(
        consent_repository,
        "get_active_consent",
        mock_get,
    )

    result = await consent_service.has_active_consent(
        conn,
        UUID(int=1),
        "transcription",
    )

    assert result is False


@pytest.mark.asyncio
async def test_require_active_consent_success(conn, monkeypatch):
    expected = {
        "status": "granted",
        "purpose": "transcription",
    }

    mock_get = AsyncMock(return_value=expected)

    monkeypatch.setattr(
        consent_repository,
        "get_active_consent",
        mock_get,
    )

    result = await consent_service.require_active_consent(
        conn,
        UUID(int=1),
        "transcription",
    )

    assert result == expected


@pytest.mark.asyncio
async def test_require_active_consent_denied(conn, monkeypatch):
    mock_get = AsyncMock(return_value=None)

    monkeypatch.setattr(
        consent_repository,
        "get_active_consent",
        mock_get,
    )

    with pytest.raises(PermissionError):
        await consent_service.require_active_consent(
            conn,
            UUID(int=1),
            "transcription",
        )


@pytest.mark.asyncio
async def test_withdraw_consent(conn, monkeypatch):
    consent_id = UUID(int=2)

    expected = {
        "id": consent_id,
        "status": "withdrawn",
    }

    mock_withdraw = AsyncMock(return_value=expected)

    monkeypatch.setattr(
        consent_repository,
        "withdraw_consent",
        mock_withdraw,
    )

    result = await consent_service.withdraw_consent(
        conn,
        consent_id,
    )

    assert result == expected

    mock_withdraw.assert_awaited_once_with(
        conn,
        consent_id,
    )


@pytest.mark.asyncio
async def test_withdraw_consent_not_active(conn, monkeypatch):
    mock_withdraw = AsyncMock(return_value=None)

    monkeypatch.setattr(
        consent_repository,
        "withdraw_consent",
        mock_withdraw,
    )

    result = await consent_service.withdraw_consent(
        conn,
        UUID(int=2),
    )

    assert result is None
