"""Turn every failure into a JSON response that still carries CORS headers.

Why this matters for the browser: an exception that escapes every handler is
answered by Starlette's outermost ServerErrorMiddleware, which sits OUTSIDE
CORSMiddleware. That 500 carries no Access-Control-Allow-Origin header, so the
browser hides it and fetch() fails with a bare "TypeError: Failed to fetch".
The UI then reports "can't reach the server" even though the server answered.
Everything here runs inside the CORS layer instead.
"""

import logging

import asyncpg
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.errors import DomainError

logger = logging.getLogger(__name__)


def _json(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail})


async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
    return _json(exc.status_code, exc.message)


async def handle_integrity_error(
    request: Request, exc: asyncpg.IntegrityConstraintViolationError
) -> JSONResponse:
    logger.warning(
        "Integrity violation on %s %s: %s (constraint=%s)",
        request.method,
        request.url.path,
        type(exc).__name__,
        getattr(exc, "constraint_name", None),
    )
    if isinstance(exc, asyncpg.UniqueViolationError):
        return _json(409, "That record already exists.")
    if isinstance(exc, asyncpg.ForeignKeyViolationError):
        return _json(422, "A record this request refers to doesn't exist.")
    if isinstance(exc, asyncpg.CheckViolationError):
        return _json(422, "One of the values was rejected as invalid.")
    return _json(409, "This change conflicts with existing data.")


async def handle_database_unavailable(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Database unavailable: %s", type(exc).__name__)
    return _json(503, "The database is temporarily unavailable. Try again shortly.")


class UnhandledErrorMiddleware(BaseHTTPMiddleware):
    """Last-resort 500 as JSON. Must be added BEFORE CORSMiddleware."""

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception:
            logger.exception("Unhandled error on %s %s", request.method, request.url.path)
            return _json(500, "Something went wrong on our side. Please try again.")


def register_error_handlers(application: FastAPI) -> None:
    application.add_exception_handler(DomainError, handle_domain_error)
    application.add_exception_handler(
        asyncpg.IntegrityConstraintViolationError, handle_integrity_error
    )
    application.add_exception_handler(
        asyncpg.PostgresConnectionError, handle_database_unavailable
    )
    application.add_exception_handler(asyncpg.InterfaceError, handle_database_unavailable)
