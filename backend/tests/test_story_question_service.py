
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services import story_question_service


@pytest.fixture
def conn():
    return AsyncMock()


@pytest.fixture
def story_id():
    return uuid4()


@pytest.fixture
def question_id():
    return uuid4()


@pytest.mark.asyncio
async def test_create_story_question(
    conn, story_id, monkeypatch
):
    expected = {"question": "What was your childhood like?"}
    mock = AsyncMock(return_value=expected)

    monkeypatch.setattr(
        story_question_service.story_question_repository,
        "create_story_question",
        mock,
    )

    result = await story_question_service.create_story_question(
        conn,
        story_id=story_id,
        question="  What was your childhood like?  ",
    )

    assert result == expected
    mock.assert_awaited_once_with(
        conn,
        story_id,
        "What was your childhood like?",
    )


@pytest.mark.asyncio
async def test_create_story_question_rejects_empty_question(
    conn, story_id
):
    with pytest.raises(ValueError, match="cannot be empty"):
        await story_question_service.create_story_question(
            conn,
            story_id=story_id,
            question="   ",
        )


@pytest.mark.asyncio
async def test_get_story_question(
    conn, question_id, monkeypatch
):
    expected = {"id": question_id}
    mock = AsyncMock(return_value=expected)

    monkeypatch.setattr(
        story_question_service.story_question_repository,
        "get_story_question_by_id",
        mock,
    )

    result = await story_question_service.get_story_question(
        conn,
        question_id,
    )

    assert result == expected


@pytest.mark.asyncio
async def test_get_story_question_returns_none(
    conn, question_id, monkeypatch
):
    mock = AsyncMock(return_value=None)

    monkeypatch.setattr(
        story_question_service.story_question_repository,
        "get_story_question_by_id",
        mock,
    )

    result = await story_question_service.get_story_question(
        conn,
        question_id,
    )

    assert result is None


@pytest.mark.asyncio
async def test_get_story_questions(
    conn, story_id, monkeypatch
):
    expected = [
        {"question": "Question one"},
        {"question": "Question two"},
    ]
    mock = AsyncMock(return_value=expected)

    monkeypatch.setattr(
        story_question_service.story_question_repository,
        "get_story_questions_by_story_id",
        mock,
    )

    result = await story_question_service.get_story_questions(
        conn,
        story_id,
    )

    assert result == expected


@pytest.mark.asyncio
async def test_update_story_question_status(
    conn, question_id, monkeypatch
):
    expected = {"status": "asked"}
    mock = AsyncMock(return_value=expected)

    monkeypatch.setattr(
        story_question_service.story_question_repository,
        "update_story_question_status",
        mock,
    )

    result = await story_question_service.update_story_question_status(
        conn,
        question_id=question_id,
        status="asked",
    )

    assert result == expected


@pytest.mark.asyncio
async def test_update_story_question_rejects_invalid_status(
    conn, question_id
):
    with pytest.raises(ValueError, match="Invalid story question status"):
        await story_question_service.update_story_question_status(
            conn,
            question_id=question_id,
            status="completed",
        )


@pytest.mark.asyncio
async def test_update_story_question_returns_none(
    conn, question_id, monkeypatch
):
    mock = AsyncMock(return_value=None)

    monkeypatch.setattr(
        story_question_service.story_question_repository,
        "update_story_question_status",
        mock,
    )

    result = await story_question_service.update_story_question_status(
        conn,
        question_id=question_id,
        status="dismissed",
    )

    assert result is None
