"""The /admin/config page and the no-login admin mode."""

from __future__ import annotations

from app.core.config import settings
from app.core.runtime_config import RuntimeConfig, config_path, load_runtime_config


def test_config_page_renders(admin_client):
    page = admin_client.get("/admin/config")
    assert page.status_code == 200
    assert "Configuração" in page.text
    assert "/admin/profiles" in page.text and "/admin/actions" in page.text


def test_config_page_saves_and_persists(admin_client):
    response = admin_client.post(
        "/admin/config",
        data={"visible_on_network": "1", "port": "6000", "start_on_logon": "1"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert load_runtime_config(config_path()) == RuntimeConfig(True, 6000, True)
    assert "6000" in admin_client.get("/admin/config").text


def test_config_page_rejects_invalid_port(admin_client):
    response = admin_client.post("/admin/config", data={"port": "70000"})
    assert response.status_code == 400
    assert "Porta inválida" in response.text


def test_config_page_is_localized(admin_client):
    english = admin_client.get("/admin/config", headers={"Accept-Language": "en"})
    assert "Settings" in english.text


def test_dashboard_redirects_to_config(admin_client):
    response = admin_client.get("/admin", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/admin/config"


def test_no_login_mode_opens_the_admin(anon_client, monkeypatch):
    monkeypatch.setattr(settings, "admin_auth_enabled", False)
    assert anon_client.get("/admin/config", follow_redirects=False).status_code == 200
    assert anon_client.get("/admin/profiles", follow_redirects=False).status_code == 200
    # The login form gives way to the settings page.
    login = anon_client.get("/admin/login", follow_redirects=False)
    assert login.status_code == 303
    assert login.headers["location"] == "/admin/config"
