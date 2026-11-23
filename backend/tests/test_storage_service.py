
from unittest.mock import MagicMock

import pytest

from app.services import storage_service


@pytest.fixture
def storage_client():
    return MagicMock()


@pytest.fixture
def storage_bucket(storage_client):
    return storage_client.storage.from_.return_value


@pytest.mark.asyncio
async def test_upload_audio_success(storage_client, storage_bucket):
    audio_data = b"sample audio data"

    size, checksum = await storage_service.upload_audio(
        storage_client,
        bucket_name="roots-audio",
        storage_key="stories/test/audio.wav",
        audio_data=audio_data,
        mime_type="audio/wav",
    )

    import hashlib

    assert size == len(audio_data)
    assert checksum == hashlib.sha256(audio_data).hexdigest()

    storage_bucket.upload.assert_called_once_with(
        path="stories/test/audio.wav",
        file=audio_data,
        file_options={
            "content-type": "audio/wav",
            "upsert": "false",
        },
    )


@pytest.mark.asyncio
async def test_upload_audio_rejects_empty_data(
    storage_client,
    storage_bucket,
):
    with pytest.raises(ValueError, match="Audio file cannot be empty"):
        await storage_service.upload_audio(
            storage_client,
            bucket_name="roots-audio",
            storage_key="stories/test/audio.wav",
            audio_data=b"",
            mime_type="audio/wav",
        )

    storage_bucket.upload.assert_not_called()


@pytest.mark.asyncio
async def test_upload_audio_storage_failure(
    storage_client,
    storage_bucket,
):
    storage_bucket.upload.side_effect = RuntimeError("Storage unavailable")

    with pytest.raises(RuntimeError, match="Storage unavailable"):
        await storage_service.upload_audio(
            storage_client,
            bucket_name="roots-audio",
            storage_key="stories/test/audio.wav",
            audio_data=b"sample audio",
            mime_type="audio/wav",
        )


@pytest.mark.asyncio
async def test_generate_download_url(
    storage_client,
    storage_bucket,
):
    storage_bucket.create_signed_url.return_value = {
        "signedURL": "https://example.com/audio"
    }

    url = await storage_service.generate_download_url(
        storage_client,
        bucket_name="roots-audio",
        storage_key="stories/test/audio.wav",
    )

    assert url == "https://example.com/audio"

    storage_bucket.create_signed_url.assert_called_once_with(
        path="stories/test/audio.wav",
        expires_in=900,
    )


@pytest.mark.asyncio
async def test_generate_download_url_rejects_invalid_expiration(
    storage_client,
    storage_bucket,
):
    with pytest.raises(ValueError):
        await storage_service.generate_download_url(
            storage_client,
            bucket_name="roots-audio",
            storage_key="stories/test/audio.wav",
            expires_in=7200,
        )

    storage_bucket.create_signed_url.assert_not_called()


@pytest.mark.asyncio
async def test_delete_audio(storage_client, storage_bucket):
    await storage_service.delete_audio(
        storage_client,
        bucket_name="roots-audio",
        storage_key="stories/test/audio.wav",
    )

    storage_bucket.remove.assert_called_once_with(
        paths=["stories/test/audio.wav"],
    )
