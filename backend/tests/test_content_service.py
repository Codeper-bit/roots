
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services import content_service


@pytest.fixture
def conn():
    return AsyncMock()


@pytest.fixture
def story_id():
    return uuid4()


@pytest.fixture
def version_id():
    return uuid4()


@pytest.fixture
def reviewer_id():
    return uuid4()


@pytest.fixture
def creator_id():
    return uuid4()


@pytest.mark.asyncio
async def test_create_first_content_version(
    conn, story_id, creator_id, monkeypatch
):
    create_mock = AsyncMock(return_value={"version_number": 1})
    latest_mock = AsyncMock(return_value=None)

    monkeypatch.setattr(
        content_service.content_version_repository,
        "get_latest_content_version",
        latest_mock,
    )
    monkeypatch.setattr(
        content_service.content_version_repository,
        "create_content_version",
        create_mock,
    )

    result = await content_service.create_content_version(
        conn,
        story_id=story_id,
        content_type="transcript",
        language_code="en",
        content="Hello world",
        origin="human_created",
        created_by=creator_id,
    )

    assert result["version_number"] == 1
    create_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_next_content_version(
    conn, story_id, monkeypatch
):
    latest_mock = AsyncMock(
        return_value={"version_number": 3}
    )
    create_mock = AsyncMock(
        return_value={"version_number": 4}
    )

    monkeypatch.setattr(
        content_service.content_version_repository,
        "get_latest_content_version",
        latest_mock,
    )
    monkeypatch.setattr(
        content_service.content_version_repository,
        "create_content_version",
        create_mock,
    )

    result = await content_service.create_content_version(
        conn,
        story_id=story_id,
        content_type="transcript",
        language_code="en",
        content="New transcript",
        origin="ai_generated",
    )

    assert result["version_number"] == 4
    assert create_mock.await_args.args[4] == 4


@pytest.mark.asyncio
async def test_create_content_strips_whitespace(
    conn, story_id, monkeypatch
):
    latest_mock = AsyncMock(return_value=None)
    create_mock = AsyncMock(return_value={"content": "Hello"})

    monkeypatch.setattr(
        content_service.content_version_repository,
        "get_latest_content_version",
        latest_mock,
    )
    monkeypatch.setattr(
        content_service.content_version_repository,
        "create_content_version",
        create_mock,
    )

    await content_service.create_content_version(
        conn,
        story_id=story_id,
        content_type="transcript",
        language_code="en",
        content="  Hello  ",
        origin="ai_generated",
    )

    assert create_mock.await_args.args[5] == "Hello"


@pytest.mark.asyncio
async def test_rejects_invalid_content_type(conn, story_id):
    with pytest.raises(ValueError, match="content type"):
        await content_service.create_content_version(
            conn,
            story_id=story_id,
            content_type="audio",
            language_code="en",
            content="Hello",
            origin="ai_generated",
        )


@pytest.mark.asyncio
async def test_rejects_invalid_origin(conn, story_id):
    with pytest.raises(ValueError, match="origin"):
        await content_service.create_content_version(
            conn,
            story_id=story_id,
            content_type="transcript",
            language_code="en",
            content="Hello",
            origin="machine_created",
        )


@pytest.mark.asyncio
async def test_rejects_empty_content(conn, story_id):
    with pytest.raises(ValueError, match="Content cannot be empty"):
        await content_service.create_content_version(
            conn,
            story_id=story_id,
            content_type="transcript",
            language_code="en",
            content="   ",
            origin="ai_generated",
        )


@pytest.mark.asyncio
async def test_human_created_requires_creator(conn, story_id):
    with pytest.raises(ValueError, match="requires a creator"):
        await content_service.create_content_version(
            conn,
            story_id=story_id,
            content_type="transcript",
            language_code="en",
            content="Hello",
            origin="human_created",
        )


@pytest.mark.asyncio
async def test_human_edited_requires_base_version(conn, story_id, creator_id):
    with pytest.raises(ValueError, match="base version"):
        await content_service.create_content_version(
            conn,
            story_id=story_id,
            content_type="transcript",
            language_code="en",
            content="Edited transcript",
            origin="human_edited",
            created_by=creator_id,
        )


@pytest.mark.asyncio
async def test_human_edited_checks_base_version(
    conn, story_id, creator_id, version_id, monkeypatch
):
    base_mock = AsyncMock(return_value=None)

    monkeypatch.setattr(
        content_service.content_version_repository,
        "get_content_version_by_id",
        base_mock,
    )

    with pytest.raises(ValueError, match="Base content version not found"):
        await content_service.create_content_version(
            conn,
            story_id=story_id,
            content_type="transcript",
            language_code="en",
            content="Edited transcript",
            origin="human_edited",
            based_on_version_id=version_id,
            created_by=creator_id,
        )


@pytest.mark.asyncio
async def test_human_edited_rejects_base_from_another_story(
    conn, story_id, creator_id, version_id, monkeypatch
):
    base_mock = AsyncMock(
        return_value={
            "story_id": uuid4(),
            "content_type": "transcript",
            "language_code": "en",
        }
    )

    monkeypatch.setattr(
        content_service.content_version_repository,
        "get_content_version_by_id",
        base_mock,
    )

    with pytest.raises(ValueError, match="another story"):
        await content_service.create_content_version(
            conn,
            story_id=story_id,
            content_type="transcript",
            language_code="en",
            content="Edited transcript",
            origin="human_edited",
            based_on_version_id=version_id,
            created_by=creator_id,
        )


@pytest.mark.asyncio
async def test_get_content_version(
    conn, version_id, monkeypatch
):
    expected = {"id": version_id}
    mock = AsyncMock(return_value=expected)

    monkeypatch.setattr(
        content_service.content_version_repository,
        "get_content_version_by_id",
        mock,
    )

    result = await content_service.get_content_version(
        conn, version_id
    )

    assert result == expected


@pytest.mark.asyncio
async def test_get_story_content_versions(
    conn, story_id, monkeypatch
):
    expected = [{"version_number": 1}, {"version_number": 2}]
    mock = AsyncMock(return_value=expected)

    monkeypatch.setattr(
        content_service.content_version_repository,
        "get_content_versions_by_story_id",
        mock,
    )

    result = await content_service.get_story_content_versions(
        conn, story_id
    )

    assert result == expected


@pytest.mark.asyncio
async def test_get_latest_content(
    conn, story_id, monkeypatch
):
    expected = {"version_number": 2}
    mock = AsyncMock(return_value=expected)

    monkeypatch.setattr(
        content_service.content_version_repository,
        "get_latest_content_version",
        mock,
    )

    result = await content_service.get_latest_content(
        conn,
        story_id=story_id,
        content_type="transcript",
        language_code="en",
    )

    assert result == expected


@pytest.mark.asyncio
async def test_review_content(
    conn, version_id, reviewer_id, monkeypatch
):
    expected = {"decision": "approved"}
    mock = AsyncMock(return_value=expected)

    monkeypatch.setattr(
        content_service.content_review_repository,
        "create_content_review",
        mock,
    )

    result = await content_service.review_content(
        conn,
        content_version_id=version_id,
        reviewer_id=reviewer_id,
        decision="approved",
        comment="Looks good.",
    )

    assert result == expected
    mock.assert_awaited_once_with(
        conn,
        version_id,
        reviewer_id,
        "approved",
        "Looks good.",
    )


@pytest.mark.asyncio
async def test_review_content_rejects_invalid_decision(
    conn, version_id, reviewer_id
):
    with pytest.raises(ValueError, match="review decision"):
        await content_service.review_content(
            conn,
            content_version_id=version_id,
            reviewer_id=reviewer_id,
            decision="pending",
        )


@pytest.mark.asyncio
async def test_review_content_returns_none_for_missing_version(
    conn, version_id, reviewer_id, monkeypatch
):
    mock = AsyncMock(return_value=None)

    monkeypatch.setattr(
        content_service.content_review_repository,
        "create_content_review",
        mock,
    )

    result = await content_service.review_content(
        conn,
        content_version_id=version_id,
        reviewer_id=reviewer_id,
        decision="approved",
    )

    assert result is None


@pytest.mark.asyncio
async def test_get_content_reviews(
    conn, version_id, monkeypatch
):
    expected = [{"decision": "approved"}]
    mock = AsyncMock(return_value=expected)

    monkeypatch.setattr(
        content_service.content_review_repository,
        "get_content_reviews_by_version_id",
        mock,
    )

    result = await content_service.get_content_reviews(
        conn, version_id
    )

    assert result == expected


@pytest.mark.asyncio
async def test_get_reviewer_history(
    conn, reviewer_id, monkeypatch
):
    expected = [{"decision": "rejected"}]
    mock = AsyncMock(return_value=expected)

    monkeypatch.setattr(
        content_service.content_review_repository,
        "get_content_reviews_by_reviewer_id",
        mock,
    )

    result = await content_service.get_reviewer_history(
        conn, reviewer_id
    )

    assert result == expected
