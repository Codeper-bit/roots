"""Translate Groq SDK failures into user-safe domain errors.

Provider messages are never echoed: they can contain request details and are
not written for end users.
"""

from __future__ import annotations

import groq

from app.core.errors import (
    DomainError,
    ServiceUnavailableError,
    UnprocessableError,
    UpstreamError,
    UpstreamTimeoutError,
)


def translate_groq_error(exc: Exception, *, task: str) -> DomainError:
    """``task`` is a noun phrase for messages, e.g. "transcription"."""
    service = f"The {task} service"

    if isinstance(exc, groq.APITimeoutError):
        return UpstreamTimeoutError(
            f"{service} took too long to respond. Try again, or use a shorter input."
        )
    if isinstance(exc, groq.APIConnectionError):
        return ServiceUnavailableError(
            f"Couldn't reach the {task} service. Try again in a moment."
        )
    if isinstance(exc, groq.APIStatusError):
        status = exc.status_code
        if status == 429:
            return ServiceUnavailableError(
                f"{service} is busy right now. Wait a minute and try again."
            )
        if status == 413:
            return UnprocessableError(f"That input is too large for the {task} service.")
        if status in (400, 422):
            return UnprocessableError(
                f"{service} couldn't process this input. "
                "Check the content and the selected language."
            )
        if status in (401, 403):
            # A configuration problem on our side; the user cannot fix it.
            return UpstreamError(f"{service} rejected our credentials.")
        if status >= 500:
            return ServiceUnavailableError(
                f"{service} is having problems. Try again shortly."
            )
    return UpstreamError(f"{service} returned an unexpected error.")
