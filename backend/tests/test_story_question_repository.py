
import pytest
import asyncpg
from uuid import uuid4

from tests import factories as f

from app.repositories.story_question_repository import (
    create_story_question,
    get_story_question_by_id,
    get_story_questions_by_story_id,
    update_story_question_status,
)


@pytest.mark.asyncio
async def test_create_story_question(conn):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    result = await create_story_question(
        conn=conn,
        story_id=story_id,
        question="What is the main lesson of this story?",
    )

    assert result is not None
    assert result["story_id"] == story_id
    assert result["question"] == "What is the main lesson of this story?"
    assert result["status"] == "suggested"
    assert result["id"] is not None
    assert result["created_at"] is not None
    assert result["updated_at"] is not None


@pytest.mark.asyncio
async def test_create_story_question_invalid_status_is_rejected(conn):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    with pytest.raises(asyncpg.CheckViolationError):
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO story_questions (
                    story_id,
                    question,
                    status
                )
                VALUES ($1, $2, $3);
                """,
                story_id,
                "What is the main lesson?",
                "invalid_status",
            )


@pytest.mark.asyncio
async def test_create_story_question_empty_question_is_rejected(conn):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    with pytest.raises(asyncpg.CheckViolationError):
        async with conn.transaction():
            await create_story_question(
                conn=conn,
                story_id=story_id,
                question="   ",
            )


@pytest.mark.asyncio
async def test_get_story_question_by_id(conn):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    question = await create_story_question(
        conn,
        story_id,
        "What happened in the story?",
    )

    result = await get_story_question_by_id(
        conn,
        question["id"],
    )

    assert result is not None
    assert result["id"] == question["id"]
    assert result["story_id"] == story_id
    assert result["question"] == "What happened in the story?"


@pytest.mark.asyncio
async def test_get_story_question_by_id_not_found(conn):
    result = await get_story_question_by_id(
        conn,
        uuid4(),
    )

    assert result is None


@pytest.mark.asyncio
async def test_get_story_questions_by_story_id(conn):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    question1 = await create_story_question(
        conn,
        story_id,
        "Who is the main character?",
    )

    question2 = await create_story_question(
        conn,
        story_id,
        "Where did the story happen?",
    )

    result = await get_story_questions_by_story_id(
        conn,
        story_id,
    )

    assert len(result) == 2

    result_ids = {item["id"] for item in result}

    assert question1["id"] in result_ids
    assert question2["id"] in result_ids


@pytest.mark.asyncio
async def test_get_story_questions_by_story_id_empty(conn):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    result = await get_story_questions_by_story_id(
        conn,
        story_id,
    )

    assert result == []


@pytest.mark.asyncio
async def test_update_story_question_status(conn):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    question = await create_story_question(
        conn,
        story_id,
        "What is the main lesson?",
    )

    result = await update_story_question_status(
        conn,
        question["id"],
        "asked",
    )

    assert result is not None
    assert result["id"] == question["id"]
    assert result["status"] == "asked"


@pytest.mark.asyncio
async def test_update_story_question_status_dismissed(conn):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    question = await create_story_question(
        conn,
        story_id,
        "Who told the story?",
    )

    result = await update_story_question_status(
        conn,
        question["id"],
        "dismissed",
    )

    assert result is not None
    assert result["status"] == "dismissed"


@pytest.mark.asyncio
async def test_update_story_question_status_not_found(conn):
    result = await update_story_question_status(
        conn,
        uuid4(),
        "asked",
    )

    assert result is None


@pytest.mark.asyncio
async def test_update_story_question_invalid_status(conn):
    owner = await f.insert_user(conn)
    story_id = await f.insert_story(conn, owner)

    question = await create_story_question(
        conn,
        story_id,
        "What happened?",
    )

    with pytest.raises(asyncpg.CheckViolationError):
        async with conn.transaction():
            await update_story_question_status(
                conn,
                question["id"],
                "invalid_status",
            )
