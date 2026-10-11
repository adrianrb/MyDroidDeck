"""MyDroidDeck server package.

The version is the single source of truth for this component and lives in
``server/version.txt`` (SemVer X.Y.Z); ``pyproject.toml`` reads it dynamically
and the API exposes it via ``/version`` and ``/health``.
"""

from __future__ import annotations

from pathlib import Path

_VERSION_FILE = Path(__file__).resolve().parents[1] / "version.txt"
_FALLBACK_VERSION = "0.1.0"


def _read_version() -> str:
    try:
        return _VERSION_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return _FALLBACK_VERSION


__version__ = _read_version()