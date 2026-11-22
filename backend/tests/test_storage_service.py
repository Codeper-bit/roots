
from unittest.mock import MagicMock

import pytest

from app.services import storage_service


@pytest.fixture
def storage_client():
    return MagicMock()


@pytest.mark.asyncio
async def test_upload_audio_success(storage_client):
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

    storage_client.put_object.assert_called_once_with(
        Bucket="roots-audio",
        Key="stories/test/audio.wav",
        Body=audio_data,
        ContentType="audio/wav",
    )


@pytest.mark.asyncio
async def test_upload_audio_rejects_empty_data(storage_client):
    with pytest.raises(ValueError, match="Audio file cannot be empty"):
        await storage_service.upload_audio(
            storage_client,
            bucket_name="roots-audio",
            storage_key="stories/test/audio.wav",
            audio_data=b"",
            mime_type="audio/wav",
        )

    storage_client.put_object.assert_not_called()


@pytest.mark.asyncio
async def test_upload_audio_storage_failure(storage_client):
    storage_client.put_object.side_effect = RuntimeError("Storage unavailable")

    with pytest.raises(RuntimeError, match="Storage unavailable"):
        await storage_service.upload_audio(
            storage_client,
            bucket_name="roots-audio",
            storage_key="stories/test/audio.wav",
            audio_data=b"sample audio",
            mime_type="audio/wav",
        )


@pytest.mark.asyncio
async def test_generate_download_url(storage_client):
    storage_client.generate_presigned_url.return_value = (
        "https://example.com/audio"
    )

    url = await storage_service.generate_download_url(
        storage_client,
        bucket_name="roots-audio",
        storage_key="stories/test/audio.wav",
    )

    assert url == "https://example.com/audio"

    storage_client.generate_presigned_url.assert_called_once_with(
        "get_object",
        Params={
            "Bucket": "roots-audio",
            "Key": "stories/test/audio.wav",
        },
        ExpiresIn=900,
    )


@pytest.mark.asyncio
async def test_generate_download_url_rejects_invalid_expiration(
    storage_client,
):
    with pytest.raises(ValueError):
        await storage_service.generate_download_url(
            storage_client,
            bucket_name="roots-audio",
            storage_key="stories/test/audio.wav",
            expires_in=7200,
        )

    storage_client.generate_presigned_url.assert_not_called()


@pytest.mark.asyncio
async def test_delete_audio(storage_client):
    await storage_service.delete_audio(
        storage_client,
        bucket_name="roots-audio",
        storage_key="stories/test/audio.wav",
    )

    storage_client.delete_object.assert_called_once_with(
        Bucket="roots-audio",
        Key="stories/test/audio.wav",
    )
