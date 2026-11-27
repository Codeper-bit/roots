import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.error_handlers import UnhandledErrorMiddleware, register_error_handlers
from app.core.config import get_settings
from app.core.database import close_pool, create_pool
from app.core.storage import create_storage_client

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
from app.api.routes.translation import router as translation_router

from app.services.groq_transcription import GroqTranscriptionEngine
from app.services.groq_translation import GroqTranslationEngine

if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    settings = get_settings()

    db_pool = await create_pool(settings)
    storage_client = create_storage_client(settings)

    transcription_engine = None
    translation_engine = None

    if settings.groq_api_key is not None:
        transcription_engine = GroqTranscriptionEngine(
            api_key=settings.groq_api_key.get_secret_value(),
            model=settings.groq_transcription_model,
            storage_client=storage_client,
            bucket_name=settings.supabase_storage_bucket,
        )
    else:
        logger.warning("GROQ_API_KEY is not set: transcription is disabled.")

    # Translation may use its own key; otherwise it shares the transcription key.
    translation_key = settings.groq_translation_api_key or settings.groq_api_key
    if translation_key is not None and settings.groq_translation_model:
        translation_engine = GroqTranslationEngine(
            api_key=translation_key.get_secret_value(),
            model=settings.groq_translation_model,
        )
    else:
        logger.warning("No Groq key/model for translation: translation is disabled.")

    application.state.settings = settings
    application.state.db_pool = db_pool
    application.state.storage_client = storage_client
    application.state.storage_bucket = settings.supabase_storage_bucket
    application.state.transcription_engine = transcription_engine
    application.state.translation_engine = translation_engine

    try:
        yield
    finally:
        if transcription_engine is not None:
            await transcription_engine.close()
        if translation_engine is not None:
            await translation_engine.close()
        await close_pool(db_pool)


def create_app() -> FastAPI:
    application = FastAPI(
        title="Roots API",
        description="Preserving family stories, languages, and cultural heritage.",
        version="1.0.0",
        lifespan=lifespan,
    )

    settings = get_settings()

    # Added first => runs INSIDE the CORS middleware added below, so even error
    # responses carry CORS headers (see app/api/error_handlers.py).
    application.add_middleware(UnhandledErrorMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(application)

    for router in (
        health_router,
        auth_router,
        stories_router,
        participants_router,
        consents_router,
        audio_router,
        processing_router,
        content_router,
        reviews_router,
        story_questions_router,
        transcription_router,
        translation_router,
    ):
        application.include_router(router)

    return application


app = create_app()
