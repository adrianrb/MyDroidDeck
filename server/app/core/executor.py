"""Execute configured actions as **Windows** programs from the WSL host.

The FastAPI server runs inside WSL2, so Windows executables are launched through
``powershell.exe`` (WSL interop) with PowerShell's ``Start-Process``: the program
starts detached, without a console window, and the helper returns immediately.

Safety: only actions that have an explicit ``ActionBinding`` (configured in the
admin UI) are ever executed. Arbitrary strings sent by paired devices are never
mapped to commands.
"""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.action import ActionBinding


def ps_literal(value: str) -> str:
    """Wrap a string in a PowerShell single-quoted literal (injection-safe)."""
    return "'" + value.replace("'", "''") + "'"


def build_ps_command(executable: str, args: str) -> str:
    """PowerShell command that launches ``executable`` detached with ``args``."""
    command = f"Start-Process -FilePath {ps_literal(executable)}"
    if args.strip():
        command += f" -ArgumentList {ps_literal(args.strip())}"
    return command


def _launch(executable: str, args: str) -> tuple[str, str | None]:
    """Launch ``executable`` on the Windows host; return ``(status, detail)``."""
    if settings.exec_engine == "dry-run":
        return "ok", "dry-run: execução simulada"
    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                build_ps_command(executable, args),
            ],
            capture_output=True,
            text=True,
            timeout=settings.exec_timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return "timeout", "O lançador excedeu o tempo limite"
    if result.returncode == 0:
        return "ok", None
    detail = (result.stderr or result.stdout or "").strip()
    return "failed", (detail.splitlines()[-1] if detail else f"exit {result.returncode}")


def execute_action(action: str, session: Session) -> tuple[str, str | None]:
    """Execute a button action on the Windows host when a binding is configured.

    Returns ``(status, detail)``: status is ``"unknown"`` when no binding exists,
    otherwise ``"ok"`` / ``"failed"`` / ``"timeout"``.
    """
    binding = session.scalar(
        select(ActionBinding).where(ActionBinding.action == action)
    )
    if binding is None:
        return "unknown", None
    status, detail = _launch(binding.executable, binding.args)
    binding.last_status = status
    binding.last_run_at = datetime.now(timezone.utc)
    session.commit()
    return status, detail