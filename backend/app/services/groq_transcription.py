import asyncio
from typing import Any

from groq import AsyncGroq
from supabase import Client


MAX_GROQ_AUDIO_SIZE = 25 * 1024 * 1024

CONTENT_TYPE_EXTENSIONS = {
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/mp4": ".mp4",
    "audio/x-m4a": ".m4a",
    "audio/m4a": ".m4a",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/wave": ".wav",
    "audio/ogg": ".ogg",
    "audio/flac": ".flac",
    "audio/webm": ".webm",
    "video/mp4": ".mp4",
}

CONTENT_TYPE_MIME = {
    "audio/mpeg": "audio/mpeg",
    "audio/mp3": "audio/mpeg",
    "audio/mp4": "audio/mp4",
    "audio/x-m4a": "audio/mp4",
    "audio/m4a": "audio/mp4",
    "audio/wav": "audio/wav",
    "audio/x-wav": "audio/wav",
    "audio/wave": "audio/wav",
    "audio/ogg": "audio/ogg",
    "audio/flac": "audio/flac",
    "audio/webm": "audio/webm",
    "video/mp4": "video/mp4",
}


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
        self.client = AsyncGroq(api_key=api_key)
        self.model = model
        self.storage_client = storage_client
        self.bucket_name = bucket_name

    async def __call__(
        self,
        *,
        audio_asset: Any,
        language_code: str | None,
    ) -> str:
        storage_key = audio_asset["storage_key"]
        content_type = audio_asset["content_type"]

        extension = CONTENT_TYPE_EXTENSIONS.get(content_type)
        mime_type = CONTENT_TYPE_MIME.get(content_type)

        if extension is None or mime_type is None:
            raise ValueError(
                f"Audio format '{content_type}' is not supported by "
                "the configured Groq transcription endpoint. "
                "Upload an MP3, WAV, M4A, MP4, OGG, FLAC, or WebM file."
            )

        # Supabase's standard Client is synchronous, so keep its download
        # operation off FastAPI's event loop.
        audio_bytes = await asyncio.to_thread(
            self.storage_client.storage
            .from_(self.bucket_name)
            .download,
            storage_key,
        )

        if not audio_bytes:
            raise ValueError("The uploaded audio file is empty.")

        if len(audio_bytes) > MAX_GROQ_AUDIO_SIZE:
            raise ValueError(
                "This audio file exceeds Groq's 25 MB free-tier "
                "upload limit. Use a smaller audio file."
            )

        request_args = {
            "file": (f"recording{extension}", audio_bytes, mime_type),
            "model": self.model,
            "response_format": "json",
            "temperature": 0.0,
        }

        if language_code:
            request_args["language"] = language_code

        result = await self.client.audio.transcriptions.create(
            **request_args
        )

        transcript = result.text.strip()

        if not transcript:
            raise ValueError("Groq returned an empty transcription.")

        return transcript

    async def close(self) -> None:
        await self.client.close()
