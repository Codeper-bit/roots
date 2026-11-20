
from collections.abc import Awaitable, Callable
from uuid import UUID

import asyncpg

from app.repositories import content_version_repository
from app.services import (
    audio_service,
    consent_service,
    processing_service,
)


TranscriptionEngine = Callable[..., Awaitable[str]]


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
    """
    Transcribe an uploaded audio asset and save the result
    as a new transcript content version.
    """

    # 1. Verify transcription consent.
    await consent_service.require_active_consent(
        conn,
        participant_id,
        "transcription",
    )

    # 2. Retrieve and validate the audio asset.
    audio_asset = await audio_service.get_audio_asset(
        conn,
        audio_asset_id,
    )

    if audio_asset is None:
        raise ValueError("Audio asset not found.")

    if audio_asset["story_id"] != story_id:
        raise ValueError("Audio asset does not belong to this story.")

    if audio_asset["upload_status"] != "uploaded":
        raise ValueError("Audio asset has not been uploaded successfully.")

    # 3. Create a processing job.
    job = await processing_service.create_processing_job(
        conn,
        story_id,
        "transcription",
        audio_asset_id,
    )

    try:
        # 4. Send the audio to the transcription engine.
        transcript_text = await transcription_engine(
            audio_asset=audio_asset,
            language_code=language_code,
        )

        if not isinstance(transcript_text, str) or not transcript_text.strip():
            raise ValueError(
                "Transcription engine returned empty or invalid text.")

        # 5. Find the latest transcript version.
        latest_version = (
            await content_version_repository.get_latest_content_version(
                conn,
                story_id,
                "transcript",
                language_code,
            )
        )

        version_number = (
            latest_version["version_number"] + 1
            if latest_version is not None
            else 1
        )

        # 6. Save the transcription as a content version.
        content_version = (
            await content_version_repository.create_content_version(
                conn,
                story_id,
                "transcript",
                language_code,
                version_number,
                transcript_text.strip(),
                "ai_generated",
                created_by=created_by,
            )
        )

        # 7. Mark the processing job as successful.
        await processing_service.update_processing_job_status(
            conn,
            job["id"],
            "succeeded",
        )

        return content_version

    except Exception as exc:
        # Mark the processing job as failed, then preserve the original error.
        try:
            await processing_service.update_processing_job_status(
                conn,
                job["id"],
                "failed",
                str(exc),
            )
        except Exception:
            pass

        raise
