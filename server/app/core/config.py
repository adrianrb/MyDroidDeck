"""Application settings, overridable via ``MYDROIDDECK_*`` env vars or ``.env``."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MYDROIDDECK_",
        env_file=".env",
        extra="ignore",
    )

    app_name: str = "MyDroidDeck"
    default_locale: str = "pt_BR"
    supported_locales: tuple[str, ...] = ("pt_BR", "en")
    database_url: str = "sqlite:///./mydroiddeck.db"
    # Shared secret that authorizes new device pairing (entered once in the app).
    # Replace before shipping; the admin UI itself is not authenticated yet.
    pairing_code: str = "pair-dev"


settings = Settings()
