
import asyncpg
from uuid import UUID

from app.repositories import story_question_repository


VALID_STATUSES = {
    "suggested",
    "asked",
    "dismissed",
}


async def create_story_question(
    conn: asyncpg.Connection,
    *,
    story_id: UUID,
    question: str,
) -> asyncpg.Record:
    """Create a question associated with a story."""

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    return await story_question_repository.create_story_question(
        conn,
        story_id,
        question.strip(),
    )


async def get_story_question(
    conn: asyncpg.Connection,
    question_id: UUID,
) -> asyncpg.Record | None:
    """Retrieve a story question by its ID."""

    return await story_question_repository.get_story_question_by_id(
        conn,
        question_id,
    )


async def get_story_questions(
    conn: asyncpg.Connection,
    story_id: UUID,
) -> list[asyncpg.Record]:
    """Retrieve all questions belonging to a story."""

    return await story_question_repository.get_story_questions_by_story_id(
        conn,
        story_id,
    )


async def update_story_question_status(
    conn: asyncpg.Connection,
    *,
    question_id: UUID,
    status: str,
) -> asyncpg.Record | None:
    """Update the status of a story question."""

    if status not in VALID_STATUSES:
        raise ValueError("Invalid story question status.")

    return await story_question_repository.update_story_question_status(
        conn,
        question_id,
        status,
    )
