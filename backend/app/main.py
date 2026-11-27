
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client

from app.core.config import get_settings
from app.core.database import create_pool

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


@asynccontextmanager
async def lifespan(application: FastAPI):
    settings = get_settings()

    # Database connection pool
    db_pool = await create_pool(settings)

    # Supabase client
    storage_client = create_storage_client(settings)

    # Groq transcription engine
    transcription_engine = None

    if settings.groq_api_key is not None:
        transcription_engine = GroqTranscriptionEngine(
            api_key=settings.groq_api_key.get_secret_value(),
            model=settings.groq_transcription_model,
            storage_client=storage_client,
            bucket_name=settings.supabase_storage_bucket,
        )

    # Groq translation engine
    translation_engine = None

    if (
        settings.groq_api_key is not None
        and getattr(settings, "groq_translation_model", None)
    ):
        translation_engine = GroqTranslationEngine(
            api_key=settings.groq_api_key.get_secret_value(),
            model=settings.groq_translation_model,
        )

    # Make dependencies available to routes
    application.state.settings = settings
    application.state.db_pool = db_pool
    application.state.storage_client = storage_client
    application.state.storage_bucket = settings.supabase_storage_bucket
    application.state.transcription_engine = transcription_engine
    application.state.translation_engine = translation_engine

    try:
        yield
    finally:
        # Close external clients and database connections
        if transcription_engine is not None:
            await transcription_engine.close()

        if translation_engine is not None:
            await translation_engine.close()

        await db_pool.close()


def create_storage_client(settings):
    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key.get_secret_value(),
    )


def create_app() -> FastAPI:
    application = FastAPI(
        title="Roots API",
        description="Preserving family stories, languages, and cultural heritage.",
        version="1.0.0",
        lifespan=lifespan,
    )

    settings = get_settings()

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routers
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
    application.include_router(translation_router)

    return application


app = create_app()
