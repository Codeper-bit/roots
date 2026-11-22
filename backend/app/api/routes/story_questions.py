from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_db_connection
from app.schemas.story_question import (
    StoryQuestionCreate,
    StoryQuestionList,
    StoryQuestionRead,
    StoryQuestionStatusUpdate,
)
from app.services import story_question_service


router = APIRouter(tags=["story-questions"])


@router.post(
    "/story-questions",
    response_model=StoryQuestionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_question(
    data: StoryQuestionCreate,
    conn: asyncpg.Connection = Depends(get_db_connection),
):
    try:
        return await story_question_service.create_story_question(
            conn,
            story_id=data.story_id,
            question=data.question,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get(
    "/story-questions/{question_id}",
    response_model=StoryQuestionRead,
)
async def get_question(
    question_id: UUID,
    conn: asyncpg.Connection = Depends(get_db_connection),
):
    question = await story_question_service.get_story_question(
        conn,
        question_id,
    )

    if question is None:
        raise HTTPException(
            status_code=404,
            detail="Story question not found.",
        )

    return question


@router.get(
    "/stories/{story_id}/questions",
    response_model=StoryQuestionList,
)
async def list_story_questions(
    story_id: UUID,
    conn: asyncpg.Connection = Depends(get_db_connection),
):
    questions = await story_question_service.get_story_questions(
        conn,
        story_id,
    )
    return {"questions": questions}


@router.patch(
    "/story-questions/{question_id}/status",
    response_model=StoryQuestionRead,
)
async def update_question_status(
    question_id: UUID,
    data: StoryQuestionStatusUpdate,
    conn: asyncpg.Connection = Depends(get_db_connection),
):
    try:
        question = await story_question_service.update_story_question_status(
            conn,
            question_id=question_id,
            status=data.status,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if question is None:
        raise HTTPException(
            status_code=404,
            detail="Story question not found.",
        )

    return question
