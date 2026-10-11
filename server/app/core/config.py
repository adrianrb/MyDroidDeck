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
    # How a dispatched action is executed on the host: "wsl" launches Windows
    # executables through WSL interop (powershell.exe + Start-Process); "dry-run"
    # only records the attempt (used by tests/CI and demos without a Windows host).
    exec_engine: str = "wsl"
    # Bounds the PowerShell launcher call, not the launched program (which detaches).
    exec_timeout_seconds: int = 20
    # Login for the server-rendered admin UI (Jinja). CHANGE these before exposing
    # the server: the admin pages can register programs the host will execute.
    admin_user: str = "admin"
    admin_password: str = "admin"
    # Signs the admin session cookie; set a stable random value in .env.
    admin_secret_key: str = "change-me"
    admin_session_seconds: int = 12 * 60 * 60


settings = Settings()
