"""Mutable runtime settings edited from the admin UI (network, port, logon).

The installed server is started by ``launch.py``, which reads this file to decide
the bind address and port; the ``/admin/config`` page writes it. The values live
outside the code tree (``MYDROIDDECK_RUNTIME_CONFIG_FILE``, default
``./data/runtime.json``) so the installer never has to edit source files.

Kept dependency-free and tolerant on read (a missing or corrupt file falls back to
defaults) so the server always starts; writes are validated and atomic.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from app.core.config import settings

# The "Stream Deck on the LAN" install ships on 56997 by default.
DEFAULT_PORT = 56997
MIN_PORT = 1
MAX_PORT = 65535


@dataclass
class RuntimeConfig:
    """Settings the user can change without reinstalling (see ``/admin/config``)."""

    visible_on_network: bool = False
    port: int = DEFAULT_PORT
    start_on_logon: bool = False

    @property
    def host(self) -> str:
        """Bind address: expose on the whole network only when asked."""
        return "0.0.0.0" if self.visible_on_network else "127.0.0.1"


def config_path() -> Path:
    """Location of the runtime config file (overridable for tests/hosts)."""
    return Path(settings.runtime_config_file)


def validate_port(value: object) -> int:
    """Return ``value`` as a valid TCP port, or raise ``ValueError``."""
    try:
        port = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise ValueError("port must be an integer") from None
    if not MIN_PORT <= port <= MAX_PORT:
        raise ValueError(f"port must be between {MIN_PORT} and {MAX_PORT}")
    return port


def _coerce_port(value: object) -> int:
    try:
        return validate_port(value)
    except ValueError:
        return DEFAULT_PORT


def load_runtime_config(path: Path | None = None) -> RuntimeConfig:
    """Read the runtime config; fall back to defaults when absent/invalid."""
    file = path or config_path()
    try:
        raw = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return RuntimeConfig()
    if not isinstance(raw, dict):
        return RuntimeConfig()
    return RuntimeConfig(
        visible_on_network=bool(raw.get("visible_on_network", False)),
        port=_coerce_port(raw.get("port", DEFAULT_PORT)),
        start_on_logon=bool(raw.get("start_on_logon", False)),
    )


def save_runtime_config(config: RuntimeConfig, path: Path | None = None) -> Path:
    """Persist ``config`` atomically so the launcher never reads a partial file."""
    file = path or config_path()
    file.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(asdict(config), indent=2, ensure_ascii=False) + "\n"

    handle, tmp_name = tempfile.mkstemp(
        dir=str(file.parent), prefix=file.name, suffix=".tmp"
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(payload)
        os.replace(tmp_name, file)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise
    return file
