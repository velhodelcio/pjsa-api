from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "pjsa-api"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://pjsa:pjsa@localhost:5432/pjsa"

    jwt_secret: str = "change-me-in-production-use-long-random-string"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    admin_seed_username: str | None = None
    admin_seed_password: str | None = None
    admin_seed_full_name: str = "Administrador"

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        if "+asyncpg" in v:
            return v
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
