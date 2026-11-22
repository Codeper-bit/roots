
import asyncio
import hashlib

from botocore.client import BaseClient


async def upload_audio(
    client: BaseClient,
    *,
    bucket_name: str,
    storage_key: str,
    audio_data: bytes,
    mime_type: str,
) -> tuple[int, str]:
    """Upload audio to object storage and return its size and SHA-256 checksum."""

    if not audio_data:
        raise ValueError("Audio file cannot be empty.")

    checksum = hashlib.sha256(audio_data).hexdigest()

    await asyncio.to_thread(
        client.put_object,
        Bucket=bucket_name,
        Key=storage_key,
        Body=audio_data,
        ContentType=mime_type,
    )

    return len(audio_data), checksum


async def generate_download_url(
    client: BaseClient,
    *,
    bucket_name: str,
    storage_key: str,
    expires_in: int = 900,
) -> str:
    """Generate a temporary URL for downloading stored audio."""

    if not 1 <= expires_in <= 3600:
        raise ValueError("URL expiration must be between 1 and 3600 seconds.")

    return await asyncio.to_thread(
        client.generate_presigned_url,
        "get_object",
        Params={
            "Bucket": bucket_name,
            "Key": storage_key,
        },
        ExpiresIn=expires_in,
    )


async def delete_audio(
    client: BaseClient,
    *,
    bucket_name: str,
    storage_key: str,
) -> None:
    """Delete an audio object from storage."""

    await asyncio.to_thread(
        client.delete_object,
        Bucket=bucket_name,
        Key=storage_key,
    )
