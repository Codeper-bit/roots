
import asyncio
import hashlib

from supabase import Client


async def upload_audio(
    client: Client,
    *,
    bucket_name: str,
    storage_key: str,
    audio_data: bytes,
    mime_type: str,
) -> tuple[int, str]:
    """Upload audio and return its size and SHA-256 checksum."""

    if not audio_data:
        raise ValueError("Audio file cannot be empty.")

    checksum = hashlib.sha256(audio_data).hexdigest()

    await asyncio.to_thread(
        client.storage.from_(bucket_name).upload,
        path=storage_key,
        file=audio_data,
        file_options={
            "content-type": mime_type,
            "upsert": "false",
        },
    )

    return len(audio_data), checksum


async def generate_download_url(
    client: Client,
    *,
    bucket_name: str,
    storage_key: str,
    expires_in: int = 900,
) -> str:
    """Generate a temporary signed download URL."""

    if not 1 <= expires_in <= 3600:
        raise ValueError(
            "URL expiration must be between 1 and 3600 seconds."
        )

    response = await asyncio.to_thread(
        client.storage.from_(bucket_name).create_signed_url,
        path=storage_key,
        expires_in=expires_in,
    )

    return response["signedURL"]


async def delete_audio(
    client: Client,
    *,
    bucket_name: str,
    storage_key: str,
) -> None:
    """Delete an audio object from storage."""

    await asyncio.to_thread(
        client.storage.from_(bucket_name).remove,
        paths=[storage_key],
    )
