"""Speech-to-text through Groq (Whisper), reading audio from private storage."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import groq
from groq import AsyncGroq
from supabase import Client

from app.core.errors import UnprocessableError, UpstreamError
from app.services.groq_errors import translate_groq_error
from app.services.speech_languages import whisper_supports

logger = logging.getLogger(__name__)

MAX_GROQ_AUDIO_SIZE = 25 * 1024 * 1024
REQUEST_TIMEOUT_SECONDS = 180.0
MAX_RETRIES = 2

# bare media type -> (file extension, MIME type sent to Groq)
_AUDIO_FORMATS: dict[str, tuple[str, str]] = {
    "audio/mpeg": (".mp3", "audio/mpeg"),
    "audio/mp3": (".mp3", "audio/mpeg"),
    "audio/mp4": (".mp4", "audio/mp4"),
    "audio/x-m4a": (".m4a", "audio/mp4"),
    "audio/m4a": (".m4a", "audio/mp4"),
    "audio/wav": (".wav", "audio/wav"),
    "audio/x-wav": (".wav", "audio/wav"),
    "audio/wave": (".wav", "audio/wav"),
    "audio/ogg": (".ogg", "audio/ogg"),
    "audio/flac": (".flac", "audio/flac"),
    "audio/webm": (".webm", "audio/webm"),
    "video/mp4": (".mp4", "video/mp4"),
}

UNSUPPORTED_FORMAT_MESSAGE = (
    "This audio format can't be transcribed. Use MP3, WAV, M4A, MP4, OGG, FLAC, or WebM."
)


def _bare_media_type(mime_type: str | None) -> str:
    """'audio/webm;codecs=opus' -> 'audio/webm'."""
    return (mime_type or "").split(";", 1)[0].strip().lower()


class GroqTranscriptionEngine:
    """Downloads audio from private Supabase Storage and transcribes it with Groq."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        storage_client: Client,
        bucket_name: str,
    ) -> None:
        self.client = AsyncGroq(
            api_key=api_key,
            timeout=REQUEST_TIMEOUT_SECONDS,
            max_retries=MAX_RETRIES,
        )
        self.model = model
        self.storage_client = storage_client
        self.bucket_name = bucket_name

    async def __call__(self, *, audio_asset: Any, language_code: str | None) -> str:
        # NOTE: the database column is mime_type, not content_type.
        fmt = _AUDIO_FORMATS.get(_bare_media_type(audio_asset["mime_type"]))
        if fmt is None:
            raise UnprocessableError(UNSUPPORTED_FORMAT_MESSAGE)
        extension, groq_mime_type = fmt

        # Reject oversized files from metadata before downloading anything.
        declared_size = audio_asset["size_bytes"]
        if declared_size is not None and declared_size > MAX_GROQ_AUDIO_SIZE:
            raise UnprocessableError(
                "This recording is larger than the 25 MB the transcription service accepts."
            )

        audio_bytes = await self._download(audio_asset["storage_key"])
        if not audio_bytes:
            raise UnprocessableError("The uploaded audio file is empty.")
        if len(audio_bytes) > MAX_GROQ_AUDIO_SIZE:
            raise UnprocessableError(
                "This recording is larger than the 25 MB the transcription service accepts."
            )

        request_args: dict[str, Any] = {
            "file": (f"recording{extension}", audio_bytes, groq_mime_type),
            "model": self.model,
            "response_format": "json",
            "temperature": 0.0,
        }
        if whisper_supports(language_code):
            request_args["language"] = language_code
        else:
            # Whisper rejects language hints it wasn't trained on (e.g. Igbo, "ig")
            # with HTTP 400. Fall back to auto-detection instead of failing.
            logger.warning(
                "Language %r is not supported by Whisper; transcribing without a language hint.",
                language_code,
            )

        try:
            result = await self.client.audio.transcriptions.create(**request_args)
        except groq.GroqError as exc:
            logger.warning(
                "Groq transcription failed (%s: %s)", type(exc).__name__, exc
            )
            raise translate_groq_error(exc, task="transcription") from exc

        transcript = (getattr(result, "text", "") or "").strip()
        if not transcript:
            raise UnprocessableError(
                "No speech could be recognised in this recording."
            )
        return transcript

    async def _download(self, storage_key: str) -> bytes:
        try:
            return await asyncio.to_thread(
                self.storage_client.storage.from_(self.bucket_name).download,
                storage_key,
            )
        except Exception as exc:  # supabase-py raises a variety of types
            logger.exception("Could not download %s from storage", storage_key)
            raise UpstreamError(
                "Couldn't read the recording from storage. Try again."
            ) from exc

    async def close(self) -> None:
        await self.client.close()
