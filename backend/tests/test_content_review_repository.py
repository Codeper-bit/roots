
import pytest

from uuid import uuid4

from tests import factories as f

from app.repositories.content_version_repository import (
    create_content_version,
)

from app.repositories.content_review_repository import (
    create_content_review,
    get_content_reviews_by_version_id,
    get_content_reviews_by_reviewer_id,
)


async def create_test_version(conn):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    version = await create_content_version(
        conn=conn,
        story_id=story_id,
        content_type="transcript",
        language_code="yo",
        version_number=1,
        content="Original transcript.",
        origin="ai_generated",
    )

    return version


@pytest.mark.asyncio
async def test_create_content_review(conn):
    version = await create_test_version(conn)
    reviewer_id = await f.insert_user(conn)

    review = await create_content_review(
        conn=conn,
        content_version_id=version["id"],
        reviewer_id=reviewer_id,
        decision="approved",
        comment="The transcript is correct.",
    )

    assert review is not None
    assert review["content_version_id"] == version["id"]
    assert review["reviewer_id"] == reviewer_id
    assert review["decision"] == "approved"
    assert review["comment"] == "The transcript is correct."

    updated_version = await conn.fetchrow(
        """
        SELECT review_status
        FROM content_versions
        WHERE id = $1;
        """,
        version["id"],
    )

    assert updated_version["review_status"] == "approved"


@pytest.mark.asyncio
async def test_create_content_review_updates_status(conn):
    version = await create_test_version(conn)
    reviewer_id = await f.insert_user(conn)

    review = await create_content_review(
        conn=conn,
        content_version_id=version["id"],
        reviewer_id=reviewer_id,
        decision="changes_requested",
        comment="Please correct the transcript.",
    )

    assert review is not None

    result = await conn.fetchval(
        """
        SELECT review_status
        FROM content_versions
        WHERE id = $1;
        """,
        version["id"],
    )

    assert result == "changes_requested"


@pytest.mark.asyncio
async def test_create_content_review_version_not_found(conn):
    reviewer_id = await f.insert_user(conn)

    review = await create_content_review(
        conn=conn,
        content_version_id=uuid4(),
        reviewer_id=reviewer_id,
        decision="approved",
    )

    assert review is None


@pytest.mark.asyncio
async def test_get_content_reviews_by_version_id(conn):
    version = await create_test_version(conn)
    reviewer_id = await f.insert_user(conn)

    first_review = await create_content_review(
        conn=conn,
        content_version_id=version["id"],
        reviewer_id=reviewer_id,
        decision="changes_requested",
        comment="Needs correction.",
    )

    second_review = await create_content_review(
        conn=conn,
        content_version_id=version["id"],
        reviewer_id=reviewer_id,
        decision="approved",
        comment="Correction looks good.",
    )

    reviews = await get_content_reviews_by_version_id(
        conn=conn,
        content_version_id=version["id"],
    )

    assert len(reviews) == 2
    assert reviews[0]["id"] == second_review["id"]
    assert reviews[1]["id"] == first_review["id"]


@pytest.mark.asyncio
async def test_get_content_reviews_by_reviewer_id(conn):
    version = await create_test_version(conn)
    reviewer_id = await f.insert_user(conn)

    review = await create_content_review(
        conn=conn,
        content_version_id=version["id"],
        reviewer_id=reviewer_id,
        decision="rejected",
        comment="The transcript needs another review.",
    )

    reviews = await get_content_reviews_by_reviewer_id(
        conn=conn,
        reviewer_id=reviewer_id,
    )

    assert len(reviews) == 1
    assert reviews[0]["id"] == review["id"]
    assert reviews[0]["decision"] == "rejected"


@pytest.mark.asyncio
async def test_get_content_reviews_by_version_id_empty(conn):
    version = await create_test_version(conn)

    reviews = await get_content_reviews_by_version_id(
        conn=conn,
        content_version_id=version["id"],
    )

    assert reviews == []


@pytest.mark.asyncio
async def test_get_content_reviews_by_reviewer_id_empty(conn):
    reviewer_id = await f.insert_user(conn)

    reviews = await get_content_reviews_by_reviewer_id(
        conn=conn,
        reviewer_id=reviewer_id,
    )

    assert reviews == []
