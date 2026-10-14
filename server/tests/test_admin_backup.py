"""Export/Import of the configuration on ``/admin/config`` (*Backup* card).

The exported JSON is what the admin downloads and posts back later, so the tests
check the file shape, the round trip (wipe → import restores everything) and the
refusal of files that are not a MyDroidDeck bundle.
"""

from __future__ import annotations

import json
import re
from datetime import datetime

from sqlalchemy import select

from app.core.runtime_config import RuntimeConfig, config_path, load_runtime_config
from app.db.session import SessionLocal
from app.i18n.translator import translate
from app.models.action import ActionBinding

FORMAT = "mydroiddeck.export"


def _bundle(**overrides) -> dict:
    """A minimal, valid bundle; ``overrides`` replaces whole sections."""
    data = {
        "format": FORMAT,
        "format_version": 1,
        "exported_at": "2026-10-13T22:15:30+00:00",
        "server_version": "0.5.3",
        "settings": {
            "visible_on_network": False,
            "port": 56997,
            "start_on_logon": False,
        },
        "actions": [
            {
                "action": "luz.mesa",
                "executable": "powershell.exe",
                "args": "-Command 1",
                "icon": None,
            }
        ],
        "profiles": [
            {
                "name": "Sala",
                "locale": "pt_BR",
                "buttons": [{"index": 0, "label": "Luz", "action": "luz.mesa"}],
            }
        ],
    }
    data.update(overrides)
    return data


def _import(admin_client, bundle, **kwargs):
    """POST a bundle as an uploaded file."""
    payload = bundle if isinstance(bundle, bytes) else json.dumps(bundle).encode()
    return admin_client.post(
        "/admin/config/import",
        files={"file": ("backup.json", payload, "application/json")},
        **kwargs,
    )


def _create_example(admin_client) -> None:
    """A profile with two buttons, an action binding and non-default settings."""
    admin_client.post(
        "/admin/actions",
        data={
            "action": "luz.mesa",
            "executable": "powershell.exe",
            "args": "-Command 1",
        },
    )
    admin_client.post(
        "/admin/profiles",
        data={
            "name": "Sala",
            "locale": "pt_BR",
            "buttons": "Luz|luz.mesa\nFoco|foco.on",
        },
    )
    admin_client.post(
        "/admin/config",
        data={"visible_on_network": "1", "port": "6123", "start_on_logon": "1"},
    )


def test_config_page_offers_export_and_import(admin_client):
    page = admin_client.get("/admin/config").text
    assert translate("admin.backup", "pt_BR") in page
    assert 'href="/admin/config/export"' in page
    assert 'action="/admin/config/import"' in page
    assert translate("admin.export", "pt_BR") in page
    assert translate("admin.import", "pt_BR") in page


def test_export_downloads_the_configuration_as_json(admin_client):
    _create_example(admin_client)

    response = admin_client.get("/admin/config/export")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.headers["cache-control"] == "no-store"
    matched = re.fullmatch(
        r'attachment; filename="mydroiddeck-(\d{8}-\d{6})\.json"',
        response.headers["content-disposition"],
    )
    assert matched
    bundle = response.json()
    # The file name and the timestamp inside it describe the same moment.
    stamp = datetime.fromisoformat(bundle["exported_at"]).astimezone()
    assert stamp.strftime("%Y%m%d-%H%M%S") == matched.group(1)
    assert bundle["format"] == FORMAT
    assert bundle["format_version"] == 1
    assert bundle["server_version"]
    assert bundle["settings"] == {
        "visible_on_network": True,
        "port": 6123,
        "start_on_logon": True,
    }
    assert bundle["actions"] == [
        {
            "action": "luz.mesa",
            "executable": "powershell.exe",
            "args": "-Command 1",
            "icon": None,
        }
    ]
    assert bundle["profiles"] == [
        {
            "name": "Sala",
            "locale": "pt_BR",
            "buttons": [
                {"index": 0, "label": "Luz", "action": "luz.mesa"},
                {"index": 1, "label": "Foco", "action": "foco.on"},
            ],
        }
    ]
    # The download is written for humans: UTF-8 kept readable, trailing newline.
    assert "Sala".encode() in admin_client.get("/admin/config/export").content


def test_import_creates_profiles_and_actions(admin_client):
    response = _import(admin_client, _bundle(), follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == (
        "/admin/config?imported=1&profiles=1&actions=1&settings=1"
    )

    page = admin_client.get(response.headers["location"]).text
    assert translate("admin.import_ok", "pt_BR").format(profiles=1, actions=1) in page
    assert "Sala" in admin_client.get("/admin/profiles").text
    assert "luz.mesa" in admin_client.get("/admin/actions").text
    profile = admin_client.get("/profiles").json()[0]
    assert [button["label"] for button in profile["buttons"]] == ["Luz"]


def test_import_updates_instead_of_duplicating(admin_client):
    admin_client.post(
        "/admin/profiles",
        data={"name": "Sala", "locale": "pt_BR", "buttons": "Antigo|x"},
    )
    admin_client.post(
        "/admin/actions", data={"action": "luz.mesa", "executable": "old.exe"}
    )

    response = _import(admin_client, _bundle(), follow_redirects=False)

    assert response.status_code == 303
    assert admin_client.get("/admin/profiles").text.count("Sala") == 1
    assert "Antigo" not in admin_client.get("/admin/profiles").text
    assert "powershell.exe" in admin_client.get("/admin/actions").text
    assert "old.exe" not in admin_client.get("/admin/actions").text
    profile = admin_client.get("/profiles").json()[0]
    assert [button["label"] for button in profile["buttons"]] == ["Luz"]


def test_import_round_trip_restores_a_wiped_configuration(admin_client):
    _create_example(admin_client)
    exported = admin_client.get("/admin/config/export").content

    # Wipe exactly what was exported: REST delete for the profile, DB for the binding.
    profile_id = admin_client.get("/profiles").json()[0]["id"]
    with SessionLocal() as session:
        for binding in session.scalars(select(ActionBinding)):
            session.delete(binding)
        session.commit()
    assert admin_client.delete(f"/profiles/{profile_id}").status_code == 204
    assert admin_client.get("/profiles").json() == []

    restored = _import(admin_client, exported, follow_redirects=False)

    assert restored.status_code == 303
    bundle = json.loads(admin_client.get("/admin/config/export").content)
    original = json.loads(exported)
    assert bundle["settings"] == original["settings"]
    assert bundle["actions"] == original["actions"]
    assert bundle["profiles"] == original["profiles"]
    assert "Sala" in admin_client.get("/admin/profiles").text


def test_import_restores_the_settings(admin_client):
    admin_client.post(
        "/admin/config",
        data={"visible_on_network": "1", "port": "6123", "start_on_logon": "1"},
    )
    bundle = _bundle(
        settings={"visible_on_network": False, "port": 6200, "start_on_logon": False}
    )

    response = _import(admin_client, bundle, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"].endswith("&settings=1")
    assert load_runtime_config(config_path()) == RuntimeConfig(False, 6200, False)
    page = admin_client.get(response.headers["location"]).text
    assert translate("admin.import_settings", "pt_BR") in page


def test_import_without_settings_leaves_the_configuration_alone(admin_client):
    admin_client.post("/admin/config", data={"port": "6123"})
    bundle = _bundle()
    del bundle["settings"]

    response = _import(admin_client, bundle, follow_redirects=False)

    assert response.status_code == 303
    assert not response.headers["location"].endswith("&settings=1")
    assert load_runtime_config(config_path()).port == 6123


def test_import_accepts_buttons_out_of_order(admin_client):
    bundle = _bundle(
        profiles=[
            {
                "name": "Sala",
                "locale": "en",
                "buttons": [
                    {"index": 1, "label": "Segundo", "action": "b"},
                    {"index": 0, "label": "Primeiro", "action": "a"},
                ],
            }
        ]
    )

    assert _import(admin_client, bundle, follow_redirects=False).status_code == 303

    profile = admin_client.get("/profiles").json()[0]
    assert profile["locale"] == "en"
    assert [button["label"] for button in profile["buttons"]] == [
        "Primeiro",
        "Segundo",
    ]


def test_import_tolerates_duplicate_entries_in_the_file(admin_client):
    bundle = _bundle(
        profiles=[
            {
                "name": "Sala",
                "locale": "pt_BR",
                "buttons": [{"label": "A", "action": "a"}],
            },
            {
                "name": "Sala",
                "locale": "pt_BR",
                "buttons": [{"label": "B", "action": "b"}],
            },
        ],
        actions=[
            {"action": "a", "executable": "one.exe"},
            {"action": "a", "executable": "two.exe"},
        ],
    )

    response = _import(admin_client, bundle, follow_redirects=False)

    assert response.status_code == 303
    actions_page = admin_client.get("/admin/actions").text
    assert "two.exe" in actions_page and "one.exe" not in actions_page
    profiles_page = admin_client.get("/admin/profiles").text
    assert profiles_page.count("Sala") == 1 and "B" in profiles_page


def test_import_rejects_files_that_are_not_a_backup(admin_client):
    cases = [
        (b"nao e json", "error.import_invalid"),
        (json.dumps({"outro": "formato"}).encode(), "error.import_invalid"),
        (json.dumps({"format": "outro.formato"}).encode(), "error.import_format"),
        (
            json.dumps({"format": FORMAT, "format_version": 99}).encode(),
            "error.import_version",
        ),
        (
            json.dumps({"format": FORMAT, "profiles": [{"name": "   "}]}).encode(),
            "error.import_invalid",
        ),
    ]

    for payload, key in cases:
        response = _import(admin_client, payload, follow_redirects=False)
        assert response.status_code == 400, payload
        assert translate(key, "pt_BR") in response.text, payload

    # A rejected file changes nothing.
    assert admin_client.get("/profiles").json() == []
    assert "luz.mesa" not in admin_client.get("/admin/actions").text


def test_import_message_is_localized(admin_client):
    response = _import(
        admin_client,
        _bundle(),
        headers={"Accept-Language": "en"},
        follow_redirects=True,
    )

    assert translate("admin.import_ok", "en").format(
        profiles=1, actions=1
    ) in response.text
    assert translate("admin.import_ok", "pt_BR").split("{")[0] not in response.text


def test_export_and_import_require_the_admin_session(anon_client):
    export = anon_client.get("/admin/config/export", follow_redirects=False)
    assert export.status_code == 303
    assert _import(anon_client, _bundle(), follow_redirects=False).status_code == 303
    # The upload is never parsed without a session: nothing was created.
    assert anon_client.get("/profiles").status_code == 401
