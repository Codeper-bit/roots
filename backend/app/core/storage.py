
import boto3
from botocore.config import Config

from app.core.config import Settings


def create_storage_client(settings: Settings):
    """Create an S3-compatible client for Cloudflare R2."""

    if not all(
        (
            settings.r2_account_id,
            settings.r2_access_key_id,
            settings.r2_secret_access_key,
            settings.r2_bucket_name,
        )
    ):
        raise RuntimeError(
            "Cloudflare R2 is not fully configured."
        )

    endpoint_url = (
        f"https://{settings.r2_account_id}.r2.cloudflarestorage.com"
    )

    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=(
            settings.r2_access_key_id.get_secret_value()
        ),
        aws_secret_access_key=(
            settings.r2_secret_access_key.get_secret_value()
        ),
        region_name="auto",
        config=Config(
            signature_version="s3v4",
            retries={
                "max_attempts": 3,
                "mode": "standard",
            },
        ),
    )
