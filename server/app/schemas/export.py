"""Pydantic schemas for the configuration bundle exported/imported by the admin.

``GET /admin/config/export`` serves this shape and ``POST /admin/config/import``
validates it back, so both sides stay in sync. The bundle carries the runtime
settings, the action bindings and the profiles (with their buttons).

Paired devices are deliberately **not** part of the bundle: the database only
keeps the SHA-256 hash of each token, so a restored server asks the phone to pair
again instead of importing anything security-sensitive.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

EXPORT_FORMAT = "mydroiddeck.export"
EXPORT_FORMAT_VERSION = 1

# Column widths of the ORM models (single place to keep them honest).
_NAME_MAX = 120
_ACTION_MAX = 120
_EXECUTABLE_MAX = 512
_ARGS_MAX = 512
_ICON_MAX = 512
_LOCALE_MAX = 10


class ExportButton(BaseModel):
    """One deck button (``label`` + the action key it dispatches)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    index: int = Field(default=0, ge=0)
    label: str = Field(max_length=_NAME_MAX)
    action: str = Field(max_length=_ACTION_MAX)


class ExportProfile(BaseModel):
    """A profile and its ordered buttons."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=_NAME_MAX)
    locale: str = Field(default="pt_BR", max_length=_LOCALE_MAX)
    buttons: list[ExportButton] = Field(default_factory=list)


class ExportAction(BaseModel):
    """A binding: the action key and the Windows program it launches."""

    model_config = ConfigDict(str_strip_whitespace=True)

    action: str = Field(min_length=1, max_length=_ACTION_MAX)
    executable: str = Field(min_length=1, max_length=_EXECUTABLE_MAX)
    args: str = Field(default="", max_length=_ARGS_MAX)
    icon: str | None = Field(default=None, max_length=_ICON_MAX)


class ExportSettings(BaseModel):
    """The ``/admin/config`` options (persisted in ``data/runtime.json``)."""

    visible_on_network: bool = False
    # Mirrors RuntimeConfig's default (app/core/runtime_config.DEFAULT_PORT).
    port: int = Field(default=56997, ge=1, le=65535)
    start_on_logon: bool = False


class ExportBundle(BaseModel):
    """The whole exported configuration (the JSON the admin downloads)."""

    format: str
    format_version: int = EXPORT_FORMAT_VERSION
    exported_at: str | None = None
    server_version: str | None = None
    settings: ExportSettings | None = None
    actions: list[ExportAction] = Field(default_factory=list)
    profiles: list[ExportProfile] = Field(default_factory=list)
