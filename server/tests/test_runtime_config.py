"""Runtime settings edited by /admin/config (network visibility, port, logon)."""

from __future__ import annotations

import pytest

from app.core.runtime_config import (
    DEFAULT_PORT,
    RuntimeConfig,
    load_runtime_config,
    save_runtime_config,
    validate_port,
)


def test_defaults_when_file_missing(tmp_path):
    config = load_runtime_config(tmp_path / "missing.json")
    assert config == RuntimeConfig()
    assert config.port == DEFAULT_PORT
    assert config.host == "127.0.0.1"


def test_roundtrip_and_host_binding(tmp_path):
    path = tmp_path / "runtime.json"
    saved = RuntimeConfig(visible_on_network=True, port=6000, start_on_logon=True)
    save_runtime_config(saved, path)
    loaded = load_runtime_config(path)
    assert loaded == saved
    assert loaded.host == "0.0.0.0"
    assert RuntimeConfig().host == "127.0.0.1"


def test_corrupt_file_falls_back_to_defaults(tmp_path):
    path = tmp_path / "runtime.json"
    path.write_text("{ not json", encoding="utf-8")
    assert load_runtime_config(path) == RuntimeConfig()


def test_invalid_values_fall_back(tmp_path):
    path = tmp_path / "runtime.json"
    path.write_text('{"port": 99999, "visible_on_network": "yes"}', encoding="utf-8")
    loaded = load_runtime_config(path)
    assert loaded.port == DEFAULT_PORT
    assert loaded.visible_on_network is True


@pytest.mark.parametrize("value", [0, 65536, -1, "abc", None])
def test_validate_port_rejects(value):
    with pytest.raises(ValueError):
        validate_port(value)


@pytest.mark.parametrize("value,expected", [(1, 1), ("56997", 56997), (65535, 65535)])
def test_validate_port_accepts(value, expected):
    assert validate_port(value) == expected


def test_save_is_atomic_and_leaves_no_temp_file(tmp_path):
    path = tmp_path / "runtime.json"
    save_runtime_config(RuntimeConfig(port=1234), path)
    assert [entry.name for entry in tmp_path.iterdir()] == ["runtime.json"]
