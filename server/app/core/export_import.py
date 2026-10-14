"""Backup of the admin-managed configuration: *Exportar…* / *Importar…*.

The bundle is the JSON the admin downloads from ``/admin/config`` and can post
back later (same machine after a wipe, or another install): runtime settings,
action bindings and profiles with their buttons.

Import is an **upsert**: profiles are matched by ``name`` and bindings by their
``action`` key, so an imported file creates what is missing and refreshes what it
brings, while anything else already in the database is kept. The uploaded file is
validated by :mod:`app.schemas.export`, which also rejects other formats/versions
with a localized message (see ``error.import_*`` keys).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.runtime_config import RuntimeConfig
from app.models.action import ActionBinding
from app.models.profile import Button, Profile
from app.schemas.export import (
    EXPORT_FORMAT,
    EXPORT_FORMAT_VERSION,
    ExportBundle,
    ExportProfile,
)


class ExportError(ValueError):
    """The uploaded file is not a usable export; ``key`` is an i18n message key."""

    def __init__(self, key: str) -> None:
        super().__init__(key)
        self.key = key


@dataclass(frozen=True)
class ImportReport:
    """How much of the bundle was applied (shown back to the admin)."""

    profiles: int
    actions: int


def export_moment() -> datetime:
    """Current local time (timezone-aware) shared by the file name and the JSON."""
    return datetime.now().astimezone()


def export_filename(moment: datetime | None = None) -> str:
    """Download name for the bundle, e.g. ``mydroiddeck-20261013-221530.json``."""
    return f"mydroiddeck-{(moment or export_moment()):%Y%m%d-%H%M%S}.json"


def _ordered_bindings(session: Session) -> list[ActionBinding]:
    """Bindings in the admin-defined order (same ordering as the actions page)."""
    return list(
        session.scalars(
            select(ActionBinding).order_by(ActionBinding.sort_order, ActionBinding.id)
        )
    )


def build_export(
    session: Session,
    config: RuntimeConfig,
    server_version: str,
    moment: datetime | None = None,
) -> dict:
    """Assemble the JSON-ready bundle (stable order, buttons in deck order)."""
    return {
        "format": EXPORT_FORMAT,
        "format_version": EXPORT_FORMAT_VERSION,
        "exported_at": (moment or export_moment()).isoformat(timespec="seconds"),
        "server_version": server_version,
        "settings": {
            "visible_on_network": config.visible_on_network,
            "port": config.port,
            "start_on_logon": config.start_on_logon,
        },
        "actions": [
            {
                "action": binding.action,
                "executable": binding.executable,
                "args": binding.args,
                "icon": binding.icon,
            }
            for binding in _ordered_bindings(session)
        ],
        "profiles": [
            {
                "name": profile.name,
                "locale": profile.locale,
                "buttons": [
                    {
                        "index": button.index,
                        "label": button.label,
                        "action": button.action,
                    }
                    for button in profile.buttons
                ],
            }
            for profile in session.scalars(select(Profile).order_by(Profile.id))
        ],
    }


def parse_export(raw: bytes) -> ExportBundle:
    """Validate an uploaded file.

    Raises :class:`ExportError` whose ``key`` is the localized message to show
    (unreadable JSON, another application's file, or a future format version).
    """
    try:
        bundle = ExportBundle.model_validate_json(raw)
    except (ValidationError, ValueError) as exc:
        raise ExportError("error.import_invalid") from exc
    if bundle.format != EXPORT_FORMAT:
        raise ExportError("error.import_format")
    if bundle.format_version != EXPORT_FORMAT_VERSION:
        raise ExportError("error.import_version")
    return bundle


def _apply_profile(
    session: Session, item: ExportProfile, existing: dict[str, Profile]
) -> Profile:
    """Create or refresh one profile, replacing its buttons with the file's list."""
    profile = existing.get(item.name)
    if profile is None:
        profile = Profile(name=item.name, locale=item.locale)
        session.add(profile)
        existing[item.name] = profile  # later duplicates in the file update this one
    profile.locale = item.locale
    # The file's order is the deck order: sort by the stored index (stable, so a
    # file without indexes keeps its own order) and re-index from zero.
    # The file's order is the deck order: sort by the stored index (stable, so a
    # file without indexes keeps its own order) and re-index from zero.
    profile.buttons = [
        Button(index=index, label=button.label, action=button.action)
        for index, button in enumerate(
            sorted(item.buttons, key=lambda button: button.index)
        )
    ]
    return profile


def apply_import(session: Session, bundle: ExportBundle) -> ImportReport:
    """Upsert the bundle's actions and profiles (settings are the caller's job)."""
    bindings = {binding.action: binding for binding in _ordered_bindings(session)}
    highest = max((binding.sort_order for binding in bindings.values()), default=-1)
    next_order = highest + 1
    for item in bundle.actions:
        binding = bindings.get(item.action)
        if binding is None:
            binding = ActionBinding(action=item.action, sort_order=next_order)
            session.add(binding)
            bindings[item.action] = binding
            next_order += 1
        binding.executable = item.executable
        binding.args = item.args
        binding.icon = item.icon or None

    profiles = {profile.name: profile for profile in session.scalars(select(Profile))}
    for item in bundle.profiles:
        _apply_profile(session, item, profiles)

    session.commit()
    return ImportReport(profiles=len(bundle.profiles), actions=len(bundle.actions))


def export_json(bundle: dict) -> str:
    """Serialize a bundle for download (UTF-8, readable, trailing newline)."""
    return json.dumps(bundle, ensure_ascii=False, indent=2) + "\n"
