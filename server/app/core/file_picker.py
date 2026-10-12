"""Native Windows file dialogs for the admin UI.

The server and the browser normally run on the **same** computer (the local,
per-user install), so the admin can ask the Windows desktop to open a real
"Open file" dialog: the chosen *path* is handed back to the form instead of
uploading the file's bytes. This is what lets the admin pick an executable
(``.exe``/``.bat``) or an icon (``.ico``/``.png``) by browsing, while the form's
text field stays editable for LAN clients where no desktop is available.

The dialog runs through ``powershell.exe`` (WSL interop on the dev host, the
bundled interpreter on the Windows install) and returns the selection as base64
on stdout, so paths with non-ASCII characters round-trip intact.
"""

from __future__ import annotations

import base64
import binascii
import logging
import subprocess

from app.core.config import settings
from app.core.executor import ps_literal

logger = logging.getLogger("mydroiddeck")

_TITLE_TOKEN = "__MYDROIDDECK_DIALOG_TITLE__"
_FILTER_TOKEN = "__MYDROIDDECK_DIALOG_FILTER__"

# WinForms needs a single-threaded apartment, hence ``-STA`` (and *not*
# ``-NonInteractive``, which would suppress the window). A topmost, invisible
# owner keeps the dialog in front of the browser; the selection is emitted as
# base64 so the caller never has to worry about the console code page.
_FILE_DIALOG_SCRIPT = """
Add-Type -AssemblyName System.Windows.Forms | Out-Null
$owner = New-Object System.Windows.Forms.Form
$owner.TopMost = $true
$owner.ShowInTaskbar = $false
$owner.WindowState = [System.Windows.Forms.FormWindowState]::Minimized
$dialog = New-Object System.Windows.Forms.OpenFileDialog
$dialog.Title = __MYDROIDDECK_DIALOG_TITLE__
$dialog.Filter = __MYDROIDDECK_DIALOG_FILTER__
$dialog.CheckFileExists = $true
$dialog.CheckPathExists = $true
$dialog.Multiselect = $false
$dialog.RestoreDirectory = $true
if ($dialog.ShowDialog($owner) -eq [System.Windows.Forms.DialogResult]::OK) {
    [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($dialog.FileName))
}
$owner.Dispose()
"""


def pick_file(title: str, filters: str) -> str | None:
    """Show a Windows "Open file" dialog and return the chosen path (or ``None``).

    ``filters`` uses the WinForms ``description|pattern|...`` syntax (already
    localized by the caller). Returns ``None`` when the user cancels, when the
    dialog fails, or under the ``dry-run`` engine (tests/demos without a desktop).
    """
    if settings.exec_engine == "dry-run":
        return None

    script = _FILE_DIALOG_SCRIPT.replace(_TITLE_TOKEN, ps_literal(title)).replace(
        _FILTER_TOKEN, ps_literal(filters)
    )
    try:
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-STA", "-Command", script],
            capture_output=True,
            timeout=settings.file_dialog_timeout_seconds,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        logger.warning("seleção de arquivo falhou: %s", exc)
        return None

    if completed.returncode != 0:
        logger.warning("seleção de arquivo retornou %s", completed.returncode)
        return None

    # Windows PowerShell writes in the console code page, not UTF-8: decode
    # leniently. The selection itself is base64 (ASCII), so this is lossless.
    stdout = completed.stdout.decode("utf-8", errors="replace")
    for line in reversed(stdout.splitlines()):
        candidate = line.strip()
        if not candidate:
            continue
        try:
            decoded = base64.b64decode(candidate, validate=True)
        except (ValueError, binascii.Error):
            continue
        return decoded.decode("utf-8", errors="replace")
    return None
