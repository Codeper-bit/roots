"""Application-level errors that map cleanly onto HTTP responses.

Services raise these instead of leaking provider or driver exceptions. Every
message is written for the end user: it must never contain API keys, signed
URLs, SQL, or raw provider payloads.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class. ``message`` is safe to show to the user."""

    status_code: int = 400

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class ForbiddenError(DomainError):
    status_code = 403


class NotFoundError(DomainError):
    status_code = 404


class ConflictError(DomainError):
    status_code = 409


class UnprocessableError(DomainError):
    status_code = 422


class UpstreamError(DomainError):
    """A dependency we call (Groq, Supabase Storage) failed."""

    status_code = 502


class ServiceUnavailableError(DomainError):
    """A dependency is temporarily unreachable or overloaded; retrying may help."""

    status_code = 503


class UpstreamTimeoutError(DomainError):
    status_code = 504
