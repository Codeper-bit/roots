
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.stories import router as stories_router
from app.api.routes.participants import router as participants_router
from app.api.routes.consents import router as consents_router
from app.api.routes.audio import router as audio_router
from app.api.routes.processing import router as processing_router
from app.api.routes.content import router as content_router
from app.api.routes.reviews import router as reviews_router
from app.api.routes.story_questions import router as story_questions_router
from app.api.routes.transcription import router as transcription_router

from app.core.config import get_settings
from app.core.database import close_pool, create_pool
from app.core.storage import create_storage_client


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    pool = await create_pool(settings)

    try:
        storage_client = create_storage_client(settings)

        app.state.db_pool = pool
        app.state.storage_client = storage_client
        app.state.storage_bucket = settings.supabase_storage_bucket

        yield

    finally:
        await close_pool(pool)


def create_app() -> FastAPI:
    application = FastAPI(
        title="Roots API",
        version="0.1.0",
        lifespan=lifespan,
    )

    application.include_router(health_router)
    application.include_router(stories_router)
    application.include_router(participants_router)
    application.include_router(consents_router)
    application.include_router(audio_router)
    application.include_router(processing_router)
    application.include_router(content_router)
    application.include_router(reviews_router)
    application.include_router(story_questions_router)
    application.include_router(transcription_router)

    return application


app = create_app()
