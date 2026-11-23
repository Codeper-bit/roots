
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["development", "test", "production"] = "development"

    # PostgreSQL configuration
    database_url: SecretStr
    db_pool_min_size: int = Field(default=2, ge=1)
    db_pool_max_size: int = Field(default=10, ge=1)
    db_command_timeout: float = Field(default=30.0, gt=0)

    # Supabase Storage configuration
    supabase_url: str
    supabase_service_role_key: SecretStr
    supabase_storage_bucket: str = "roots-audio"

    @field_validator("database_url")
    @classmethod
    def _check_database_url_scheme(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().startswith(
            ("postgresql://", "postgres://")
        ):
            raise ValueError(
                "DATABASE_URL must start with postgresql:// or postgres://"
            )
        return value

    @field_validator("supabase_url")
    @classmethod
    def _check_supabase_url(cls, value: str) -> str:
        if not value.startswith(("https://", "http://")):
            raise ValueError(
                "SUPABASE_URL must be a valid HTTP or HTTPS URL."
            )
        return value.rstrip("/")

    @model_validator(mode="after")
    def _check_pool_sizes(self) -> "Settings":
        if self.db_pool_min_size > self.db_pool_max_size:
            raise ValueError(
                "DB_POOL_MIN_SIZE cannot be greater than DB_POOL_MAX_SIZE"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Load settings once and reuse them."""
    return Settings()
