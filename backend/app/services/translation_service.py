
from collections.abc import Awaitable, Callable
from uuid import UUID

import asyncpg

from app.repositories import content_version_repository
from app.services import consent_service, processing_service


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
        raise ValueError("Participant does not belong to this story.")

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
        raise ValueError("Source transcript not found.")

    if source_version["story_id"] != story_id:
        raise ValueError("Transcript does not belong to this story.")

    if source_version["content_type"] != "transcript":
        raise ValueError("The selected content version is not a transcript.")

    source_language = source_version["language_code"]

    if source_language == target_language_code:
        raise ValueError("Source and target languages must be different.")

    # Create a processing job.
    job = await processing_service.create_processing_job(
        conn,
        story_id,
        "translation",
    )

    try:
        translated_text = await translation_engine(
            text=source_version["content"],
            source_language=source_language,
            target_language=target_language_code,
        )

        if not translated_text or not translated_text.strip():
            raise ValueError("Translation returned empty content.")

        # Number translations independently for each target language.
        latest_version = (
            await content_version_repository.get_latest_content_version(
                conn,
                story_id,
                "translation",
                target_language_code,
            )
        )

        version_number = (
            latest_version["version_number"] + 1
            if latest_version
            else 1
        )

        # Save a NEW version. Never overwrite the original transcript.
        translated_version = (
            await content_version_repository.create_content_version(
                conn,
                story_id=story_id,
                content_type="translation",
                language_code=target_language_code,
                version_number=version_number,
                content=translated_text.strip(),
                origin="ai_generated",
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

    except Exception:
        try:
            await processing_service.update_processing_job_status(
                conn,
                job["id"],
                "failed",
                "Translation processing failed.",
            )
        except Exception:
            pass

        raise
