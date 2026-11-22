
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

    database_url: SecretStr
    db_pool_min_size: int = Field(default=2, ge=1)
    db_pool_max_size: int = Field(default=10, ge=1)
    db_command_timeout: float = Field(default=30.0, gt=0)

    # Cloudflare R2 configuration (optional until storage is configured).
    r2_account_id: str | None = None
    r2_access_key_id: SecretStr | None = None
    r2_secret_access_key: SecretStr | None = None
    r2_bucket_name: str | None = None

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

    @model_validator(mode="after")
    def _check_pool_sizes(self) -> "Settings":
        if self.db_pool_min_size > self.db_pool_max_size:
            raise ValueError(
                "DB_POOL_MIN_SIZE cannot be greater than DB_POOL_MAX_SIZE"
            )
        return self

    @model_validator(mode="after")
    def _check_r2_configuration(self) -> "Settings":
        r2_values = (
            self.r2_account_id,
            self.r2_access_key_id,
            self.r2_secret_access_key,
            self.r2_bucket_name,
        )

        if any(value is not None for value in r2_values):
            if not all(value is not None for value in r2_values):
                raise ValueError(
                    "All R2 settings must be provided when configuring storage."
                )

        return self


@lru_cache
def get_settings() -> Settings:
    """Load settings once and reuse them. Tests can call get_settings.cache_clear()."""
    return Settings()
