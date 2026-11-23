from supabase import Client, create_client

from app.core.config import Settings


def create_storage_client(settings: Settings) -> Client:
    """Create a Supabase client for private object storage."""

    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key.get_secret_value(),
    )
