import asyncio
import logging
from collections.abc import Awaitable, Callable
from uuid import UUID

import asyncpg

from app.core.errors import DomainError, NotFoundError, UnprocessableError
from app.repositories import content_version_repository, language_repository
from app.services import (
    audio_service,
    consent_service,
    processing_service,
)

logger = logging.getLogger(__name__)

TranscriptionEngine = Callable[..., Awaitable[str]]

GENERIC_FAILURE_MESSAGE = "The transcription failed unexpectedly. Please try again."


async def _mark_job_failed(
    conn: asyncpg.Connection,
    job_id: UUID,
    message: str,
) -> None:
    """Record a failure without ever masking the original error."""
    try:
        await processing_service.update_processing_job_status(
            conn, job_id, "failed", message
        )
    except Exception:
        logger.exception("Could not mark processing job %s as failed", job_id)


async def transcribe_audio(
    conn: asyncpg.Connection,
    *,
    participant_id: UUID,
    story_id: UUID,
    audio_asset_id: UUID,
    language_code: str,
    transcription_engine: TranscriptionEngine,
    created_by: UUID | None = None,
) -> asyncpg.Record:
    """Transcribe an uploaded audio asset and save the result as a new transcript version."""

    # 1. Verify the participant belongs to this story and consented.
    participant = await conn.fetchrow(
        "SELECT id FROM story_participants WHERE id = $1 AND story_id = $2",
        participant_id,
        story_id,
    )
    if participant is None:
        raise UnprocessableError("That participant does not belong to this story.")

    await consent_service.require_active_consent(
        conn,
        participant_id,
        "transcription",
    )

    # 2. Retrieve and validate the audio asset.
    audio_asset = await audio_service.get_audio_asset(conn, audio_asset_id)

    if audio_asset is None or audio_asset["story_id"] != story_id:
        # Same answer for "missing" and "someone else's" so ids can't be probed.
        raise NotFoundError("Audio asset not found.")

    if audio_asset["upload_status"] != "uploaded":
        raise UnprocessableError("Audio asset has not been uploaded successfully.")

    # 3. The transcript is stored under this language; it must exist in the table.
    if not await language_repository.is_language_available(conn, language_code):
        raise UnprocessableError(
            f"The language '{language_code}' isn't available yet. "
            "Pick one from the list."
        )

    # 4. Create a processing job and mark it running.
    job = await processing_service.create_processing_job(
        conn,
        story_id,
        "transcription",
        audio_asset_id,
    )
    await processing_service.update_processing_job_status(conn, job["id"], "running")

    try:
        # 5. Send the audio to the transcription engine.
        transcript_text = await transcription_engine(
            audio_asset=audio_asset,
            language_code=language_code,
        )

        if not isinstance(transcript_text, str) or not transcript_text.strip():
            raise UnprocessableError("Transcription engine returned empty text.")

        # 6. Save as the next version (race-free numbering).
        content_version = await content_version_repository.create_next_content_version(
            conn,
            story_id,
            "transcript",
            language_code,
            transcript_text.strip(),
            "ai_generated",
            created_by=created_by,
        )

        # 7. Mark the processing job as successful.
        await processing_service.update_processing_job_status(
            conn, job["id"], "succeeded"
        )
        return content_version

    except asyncio.CancelledError:
        # Client disconnected mid-request: don't leave the job 'running' forever.
        await asyncio.shield(
            _mark_job_failed(conn, job["id"], "The transcription was interrupted.")
        )
        raise
    except DomainError as exc:
        await _mark_job_failed(conn, job["id"], exc.message)
        raise
    except Exception:
        logger.exception("Transcription job %s failed", job["id"])
        await _mark_job_failed(conn, job["id"], GENERIC_FAILURE_MESSAGE)
        raise
