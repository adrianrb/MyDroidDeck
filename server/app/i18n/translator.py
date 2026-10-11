"""Tiny JSON-catalog i18n with pt-BR as the default locale.

Deliberately dependency-free: catalogs live in ``i18n/locales/<locale>.json`` and
are keyed by message id. Swap for Babel/gettext if the catalog grows.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

LOCALES_DIR = Path(__file__).parent / "locales"
DEFAULT_LOCALE = "pt_BR"


@lru_cache(maxsize=None)
def _catalog(locale: str) -> dict[str, str]:
    path = LOCALES_DIR / f"{locale}.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def negotiate(accept_language: str | None) -> str:
    """Pick the first supported locale from an ``Accept-Language`` header."""
    if not accept_language:
        return DEFAULT_LOCALE
    for part in accept_language.split(","):
        tag = part.split(";")[0].strip().replace("-", "_")
        if (LOCALES_DIR / f"{tag}.json").is_file():
            return tag
    return DEFAULT_LOCALE


def translate(key: str, locale: str | None = None) -> str:
    """Return the message for ``key``, falling back to the default locale."""
    locale = locale or DEFAULT_LOCALE
    return _catalog(locale).get(key) or _catalog(DEFAULT_LOCALE).get(key, key)
