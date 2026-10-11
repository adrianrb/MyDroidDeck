"""Extract the *real* icon of a Windows executable, for the deck buttons.

The deck's buttons reference action keys; each key is bound (in the admin UI) to a
Windows executable. To draw the program's own icon on the button, the server asks
the Windows host — through WSL interop — to render the executable's associated icon
as a PNG (base64-encoded on stdout, so no shared filesystem path is needed), caches
it on disk, and ``GET /icon?action=`` serves it to the app.

Icons are extracted lazily on first request and cached per executable, so the
PowerShell call happens only once per program.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import logging
import re
import subprocess
from collections.abc import Iterable
from pathlib import Path

from app.core.config import settings
from app.core.executor import ps_literal

logger = logging.getLogger("mydroiddeck")

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_BASE64_LINE = re.compile(r"[A-Za-z0-9+/=]{16,}")

# Renders the icon associated with a program (works for .exe/.dll). Bare names like
# "notepad.exe" are resolved through Get-Command first; Store apps (Paint, …) expose a
# 0-byte alias under WindowsApps that the interop PATH does not search, so the alias is
# looked up explicitly. The PNG comes back as base64 on stdout.
_PS_SCRIPT = """
Add-Type -AssemblyName System.Drawing
$path = {path}
if (-not (Test-Path -LiteralPath $path)) {{
    $cmd = Get-Command $path -ErrorAction SilentlyContinue
    if ($null -ne $cmd) {{
        $path = $cmd.Source
    }} else {{
        $alias = Join-Path $env:LOCALAPPDATA ("Microsoft\\WindowsApps\\" + (Split-Path -Leaf $path))
        if (Test-Path -LiteralPath $alias) {{ $path = $alias }} else {{ exit 3 }}
    }}
}}
$icon = [System.Drawing.Icon]::ExtractAssociatedIcon($path)
if ($null -eq $icon) {{ exit 4 }}
$stream = New-Object System.IO.MemoryStream
$icon.ToBitmap().Save($stream, [System.Drawing.Imaging.ImageFormat]::Png)
[Convert]::ToBase64String($stream.ToArray())
"""


def cache_dir() -> Path:
    """Directory holding the extracted PNG icons."""
    return Path(settings.icon_cache_dir)


def windows_path(path: Path) -> str:
    """Translate a WSL path under ``/mnt/<drive>`` to its Windows form.

    ``/mnt/c/Desenv/app.exe`` -> ``C:\\\\Desenv\\\\app.exe``; anything else is kept
    as-is.
    """
    resolved = path.resolve()
    parts = resolved.parts
    if len(parts) > 3 and parts[0] == "/" and parts[1] == "mnt" and len(parts[2]) == 1:
        drive = parts[2].upper()
        return f"{drive}:\\" + "\\".join(parts[3:])
    return str(resolved)


def host_path(executable: str) -> str:
    """Accept both Windows (``C:\\...``) and WSL (``/mnt/c/...``) executable paths."""
    return windows_path(Path(executable)) if executable.startswith("/") else executable


def icon_cache_file(executable: str) -> Path:
    """Stable cache path for ``executable`` (same program -> same file)."""
    digest = hashlib.sha256(executable.strip().lower().encode("utf-8")).hexdigest()[:16]
    return cache_dir() / f"{digest}.png"


def extract_icon(executable: str) -> Path | None:
    """Return the cached PNG icon for ``executable``, extracting it on first use.

    Returns ``None`` when there is nothing to extract (empty path, dry-run engine,
    program without an icon, or a failed extraction).
    """
    if not executable.strip():
        return None

    target = icon_cache_file(executable)
    if target.is_file():
        return target

    if settings.exec_engine == "dry-run":
        return None

    png = _render_icon(host_path(executable.strip()))
    if png is None:
        return None

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(png)
    return target


def prewarm_icons(executables: Iterable[str]) -> None:
    """Extract (and cache) the icons of ``executables``, ignoring failures.

    Meant to run as a background task right after the admin registers bindings, so
    the deck's first load already finds the icons cached.
    """
    for executable in executables:
        try:
            extract_icon(executable)
        except Exception:  # pragma: no cover - best effort, never breaks the request
            logger.warning("falha ao pré-aquecer o ícone de %s", executable)


def _render_icon(host_executable: str) -> bytes | None:
    """Ask the Windows host for the program's icon; return the PNG bytes."""
    script = _PS_SCRIPT.format(path=ps_literal(host_executable))
    try:
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            timeout=settings.exec_timeout_seconds,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        logger.warning("extração de ícone falhou para %s: %s", host_executable, exc)
        return None

    if completed.returncode != 0:
        logger.warning(
            "extração de ícone retornou %s para %s", completed.returncode, host_executable
        )
        return None

    for line in reversed(completed.stdout.splitlines()):
        candidate = line.strip()
        if not _BASE64_LINE.fullmatch(candidate):
            continue
        try:
            data = base64.b64decode(candidate)
        except (ValueError, binascii.Error):
            continue
        if data.startswith(PNG_MAGIC):
            return data

    logger.warning("saída inesperada ao extrair o ícone de %s", host_executable)
    return None
