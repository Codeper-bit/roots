
import logging
from collections.abc import Awaitable, Callable
from uuid import UUID

import asyncpg

from app.core.errors import DomainError, NotFoundError, UnprocessableError
from app.repositories import content_version_repository, language_repository
from app.services import consent_service, processing_service

logger = logging.getLogger(__name__)

GENERIC_FAILURE_MESSAGE = "The translation failed unexpectedly. Please try again."


TranslationEngine = Callable[..., Awaitable[str]]


async def translate_content(
    conn: asyncpg.Connection,
    *,
    story_id: UUID,
    participant_id: UUID,
    source_version_id: UUID,
    target_language_code: str,
    translation_engine: TranslationEngine,
    created_by: UUID,
) -> asyncpg.Record:

    # Verify the participant belongs to this story.
    participant = await conn.fetchrow(
        """
        SELECT id
        FROM story_participants
        WHERE id = $1 AND story_id = $2
        """,
        participant_id,
        story_id,
    )

    if participant is None:
        raise UnprocessableError("Participant does not belong to this story.")

    # Translation requires its own explicit consent.
    await consent_service.require_active_consent(
        conn,
        participant_id,
        "translation",
    )

    # Retrieve the original transcript.
    source_version = (
        await content_version_repository.get_content_version_by_id(
            conn,
            source_version_id,
        )
    )

    if source_version is None:
        raise NotFoundError("Source transcript not found.")

    if source_version["story_id"] != story_id:
        raise NotFoundError("Source transcript not found.")

    if source_version["content_type"] != "transcript":
        raise UnprocessableError("The selected content version is not a transcript.")

    source_language = source_version["language_code"]

    if source_language == target_language_code:
        raise UnprocessableError("Source and target languages must be different.")

    if not await language_repository.is_language_available(conn, target_language_code):
        raise UnprocessableError(
            f"The language '{target_language_code}' isn't available yet."
        )

    # Create a processing job.
    job = await processing_service.create_processing_job(
        conn,
        story_id,
        "translation",
    )
    await processing_service.update_processing_job_status(conn, job["id"], "running")

    try:
        translated_text = await translation_engine(
            text=source_version["content"],
            source_language=source_language,
            target_language=target_language_code,
        )

        if not translated_text or not translated_text.strip():
            raise UnprocessableError("Translation returned empty content.")

        # Save a NEW version (race-free numbering). Never overwrite the original.
        translated_version = (
            await content_version_repository.create_next_content_version(
                conn,
                story_id,
                "translation",
                target_language_code,
                translated_text.strip(),
                "ai_generated",
                based_on_version_id=source_version_id,
                created_by=created_by,
            )
        )

        await processing_service.update_processing_job_status(
            conn,
            job["id"],
            "succeeded",
        )

        return translated_version

    except DomainError as exc:
        await _mark_failed(conn, job["id"], exc.message)
        raise
    except Exception:
        logger.exception("Translation job %s failed", job["id"])
        await _mark_failed(conn, job["id"], GENERIC_FAILURE_MESSAGE)
        raise


async def _mark_failed(conn: asyncpg.Connection, job_id: UUID, message: str) -> None:
    try:
        await processing_service.update_processing_job_status(
            conn, job_id, "failed", message
        )
    except Exception:
        logger.exception("Could not mark processing job %s as failed", job_id)
