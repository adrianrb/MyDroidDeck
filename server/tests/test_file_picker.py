"""Native Windows file dialog used by the admin to pick paths.

The interactive dialog itself is exercised on a real desktop; here we cover the
contract around it hermetically: no-op without a Windows host, and the
base64/UTF-8 decoding of the chosen path (so accented paths round-trip).
"""

import base64

from app.core import file_picker


def test_pick_file_is_a_noop_in_dry_run():
    # The suite runs with MYDROIDDECK_EXEC_ENGINE=dry-run: never open a dialog.
    assert file_picker.pick_file("Selecione", "Executáveis|*.exe|Todos|*.*") is None


def _result(stdout: bytes, returncode: int = 0):
    class Result:
        pass

    result = Result()
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = b""
    return result


def test_pick_file_decodes_the_chosen_path(monkeypatch):
    monkeypatch.setattr(file_picker.settings, "exec_engine", "wsl")
    chosen = "C:\\Minha Ação\\programa.exe"
    encoded = base64.b64encode(chosen.encode("utf-8")) + b"\n"
    monkeypatch.setattr(file_picker.subprocess, "run", lambda *a, **k: _result(encoded))

    assert file_picker.pick_file("Título", "*.exe|*.exe") == chosen


def test_pick_file_returns_none_when_cancelled(monkeypatch):
    monkeypatch.setattr(file_picker.settings, "exec_engine", "wsl")
    monkeypatch.setattr(file_picker.subprocess, "run", lambda *a, **k: _result(b"\n"))

    assert file_picker.pick_file("Título", "*.exe|*.exe") is None


def test_pick_file_returns_none_on_error(monkeypatch):
    monkeypatch.setattr(file_picker.settings, "exec_engine", "wsl")
    monkeypatch.setattr(file_picker.subprocess, "run", lambda *a, **k: _result(b"", 1))

    assert file_picker.pick_file("Título", "*.exe|*.exe") is None
