"""Icon extraction/serving: the deck draws the program's real icon on each button."""

import shutil
from pathlib import Path

import pytest

from app.core.config import settings
from app.core.icons import (
    PNG_MAGIC,
    extract_icon,
    host_path,
    icon_cache_file,
    prewarm_icons,
    windows_path,
)

POWERSHELL = shutil.which("powershell.exe")
NOTEPAD = Path("/mnt/c/Windows/System32/notepad.exe")
# Store apps (Windows 11 Paint) are reachable only through a WindowsApps alias.
STORE_APP_ALIAS = next(
    iter(Path("/mnt/c/Users").glob("*/AppData/Local/Microsoft/WindowsApps/mspaint.exe")),
    None,
)


def _bind(client, action="bloco.notas", executable="notepad.exe"):
    return client.post(
        "/admin/actions",
        data={"action": action, "executable": executable, "args": ""},
        follow_redirects=False,
    )


def _png_size(path: Path) -> tuple[int, int]:
    """Width/height from the PNG IHDR chunk, without an image library."""
    data = path.read_bytes()
    assert data[:8] == PNG_MAGIC
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


def test_windows_path_translates_mnt_drives():
    assert windows_path(Path("/mnt/c/Desenv/app.exe")) == "C:\\Desenv\\app.exe"


def test_windows_path_keeps_paths_outside_mnt():
    assert windows_path(Path("/tmp/opencode/app.exe")).startswith("/")


def test_host_path_accepts_windows_and_wsl_style_paths():
    assert host_path("C:\\Windows\\notepad.exe") == "C:\\Windows\\notepad.exe"
    assert host_path("/mnt/c/Windows/notepad.exe") == "C:\\Windows\\notepad.exe"


def test_icon_cache_file_is_stable_per_executable():
    assert icon_cache_file("notepad.exe") == icon_cache_file("  notepad.exe  ")
    assert icon_cache_file("notepad.exe") != icon_cache_file("calc.exe")
    assert icon_cache_file("notepad.exe").suffix == ".png"


def test_icon_requires_a_paired_device(anon_client):
    response = anon_client.get("/icon", params={"action": "bloco.notas"})
    assert response.status_code == 401


def test_unknown_action_has_no_icon(client):
    response = client.get("/icon", params={"action": "nao.configurada"})
    assert response.status_code == 404


def test_binding_without_extractable_icon_answers_404(admin_client):
    assert _bind(admin_client).status_code == 303
    response = admin_client.get("/icon", params={"action": "bloco.notas"})
    assert response.status_code == 404


def test_prewarm_icons_never_raises_when_extraction_fails():
    prewarm_icons(["programa.que.nao.existe.exe", "", "outro.exe"])
    assert not icon_cache_file("programa.que.nao.existe.exe").is_file()


@pytest.mark.skipif(
    POWERSHELL is None or not NOTEPAD.is_file(), reason="precisa de um host Windows"
)
def test_extracts_a_real_icon_from_a_windows_executable(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "exec_engine", "wsl")
    monkeypatch.setattr(settings, "icon_cache_dir", str(tmp_path))

    icon = extract_icon("C:\\Windows\\System32\\notepad.exe")

    assert icon is not None
    assert icon.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert icon.stat().st_size > 0
    # Second call is served from the cache (same file, no new extraction).
    assert extract_icon("C:\\Windows\\System32\\notepad.exe") == icon


@pytest.mark.skipif(
    POWERSHELL is None or not NOTEPAD.is_file(), reason="precisa de um host Windows"
)
def test_extracts_a_high_resolution_icon(tmp_path, monkeypatch):
    # The shell's jumbo image list keeps the deck keys crisp; a plain
    # ExtractAssociatedIcon (the fallback) would cap the icon at 32x32.
    monkeypatch.setattr(settings, "exec_engine", "wsl")
    monkeypatch.setattr(settings, "icon_cache_dir", str(tmp_path))

    icon = extract_icon("C:\\Windows\\System32\\notepad.exe")

    assert icon is not None
    width, height = _png_size(icon)
    assert width == height
    assert width >= 48


@pytest.mark.skipif(
    POWERSHELL is None or STORE_APP_ALIAS is None,
    reason="Paint (app da Store) não disponível neste host",
)
def test_extracts_the_icon_of_a_store_app_alias(tmp_path, monkeypatch):
    # "mspaint.exe" is not on the interop PATH: only the WindowsApps alias resolves it.
    monkeypatch.setattr(settings, "exec_engine", "wsl")
    monkeypatch.setattr(settings, "icon_cache_dir", str(tmp_path))

    icon = extract_icon("mspaint.exe")

    assert icon is not None
    assert icon.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
