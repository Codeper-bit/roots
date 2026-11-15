import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.health import router as health_router

from app.core.config import get_settings
from app.core.database import close_pool, create_pool

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    pool = await create_pool(settings)

    app.state.db_pool = pool
    try:
        yield
    finally:
        await close_pool(pool)


def create_app() -> FastAPI:
    application = FastAPI(title="Roots API", version="0.1.0", lifespan=lifespan)
    application.include_router(health_router)
    return application


app = create_app()
