
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
from app.api.routes.auth import router as auth_router

from app.core.config import get_settings
from app.core.database import close_pool, create_pool
from app.core.storage import create_storage_client

from app.services.groq_transcription import GroqTranscriptionEngine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    pool = await create_pool(settings)
    transcription_engine = None

    try:
        storage_client = create_storage_client(settings)

        if settings.groq_api_key is not None:
            transcription_engine = GroqTranscriptionEngine(
                api_key=settings.groq_api_key.get_secret_value(),
                model=settings.groq_transcription_model,
                storage_client=storage_client,
                bucket_name=settings.supabase_storage_bucket,
            )

        app.state.db_pool = pool
        app.state.storage_client = storage_client
        app.state.storage_bucket = settings.supabase_storage_bucket
        app.state.transcription_engine = transcription_engine

        yield

    finally:
        if transcription_engine is not None:
            await transcription_engine.close()

        await close_pool(pool)


def create_app() -> FastAPI:
    application = FastAPI(
        title="Roots API",
        version="0.1.0",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health_router)
    application.include_router(auth_router)
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
