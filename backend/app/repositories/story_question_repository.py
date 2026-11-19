
import asyncpg
from uuid import UUID


async def create_story_question(
    conn: asyncpg.Connection,
    story_id: UUID,
    question: str,
) -> asyncpg.Record:
    return await conn.fetchrow(
        """
        INSERT INTO story_questions (
            story_id,
            question
        )
        VALUES ($1, $2)
        RETURNING *;
        """,
        story_id,
        question,
    )


async def get_story_question_by_id(
    conn: asyncpg.Connection,
    question_id: UUID,
) -> asyncpg.Record | None:
    return await conn.fetchrow(
        """
        SELECT *
        FROM story_questions
        WHERE id = $1;
        """,
        question_id,
    )


async def get_story_questions_by_story_id(
    conn: asyncpg.Connection,
    story_id: UUID,
) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT *
        FROM story_questions
        WHERE story_id = $1
        ORDER BY created_at DESC;
        """,
        story_id,
    )


async def update_story_question_status(
    conn: asyncpg.Connection,
    question_id: UUID,
    status: str,
) -> asyncpg.Record | None:
    return await conn.fetchrow(
        """
        UPDATE story_questions
        SET status = $2
        WHERE id = $1
        RETURNING *;
        """,
        question_id,
        status,
    )
