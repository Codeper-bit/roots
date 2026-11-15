import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_load_database_url_from_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://roots:secret@localhost:5432/roots_test")
    monkeypatch.setenv("DB_POOL_MIN_SIZE", "3")
    monkeypatch.setenv("DB_POOL_MAX_SIZE", "8")

    settings = Settings()

    assert settings.database_url.get_secret_value() == (
        "postgresql://roots:secret@localhost:5432/roots_test"
    )
    assert settings.db_pool_min_size == 3
    assert settings.db_pool_max_size == 8


def test_settings_reject_missing_database_url(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValidationError):
        Settings()


def test_settings_reject_non_postgresql_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "mysql://user:pass@localhost/database")

    with pytest.raises(ValidationError, match="DATABASE_URL must start"):
        Settings()


def test_settings_reject_minimum_pool_larger_than_maximum(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://roots:secret@localhost:5432/roots_test")
    monkeypatch.setenv("DB_POOL_MIN_SIZE", "5")
    monkeypatch.setenv("DB_POOL_MAX_SIZE", "2")

    with pytest.raises(ValidationError, match="DB_POOL_MIN_SIZE cannot be greater"):
        Settings()
