import base64

from app.core.config import settings

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


def test_admin_requires_login(anon_client):
    response = anon_client.get("/admin/profiles", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/login"


def test_admin_login_rejects_bad_credentials(anon_client):
    response = anon_client.post(
        "/admin/login",
        data={"username": settings.admin_user, "password": "errada"},
        follow_redirects=False,
    )
    assert response.status_code == 401
    assert "inválidos" in response.text.lower()
    # A failed login must not grant access.
    assert (
        anon_client.get("/admin/profiles", follow_redirects=False).status_code == 303
    )


def test_admin_logout_revokes_session(anon_client):
    anon_client.post(
        "/admin/login",
        data={"username": settings.admin_user, "password": settings.admin_password},
        follow_redirects=False,
    )
    assert anon_client.get("/admin/profiles", follow_redirects=False).status_code == 200

    anon_client.post("/admin/logout", follow_redirects=False)
    assert anon_client.get("/admin/profiles", follow_redirects=False).status_code == 303


def test_admin_tampered_cookie_is_rejected(anon_client):
    anon_client.cookies.set("mydroiddeck_admin", "1234567890.deadbeef")
    assert anon_client.get("/admin/profiles", follow_redirects=False).status_code == 303


def test_session_token_roundtrip_and_tamper():
    from app.core.admin_auth import create_session_token, verify_session_token

    token = create_session_token()
    assert verify_session_token(token)
    assert not verify_session_token(token + "0")
    assert not verify_session_token("sem-assinatura")
    assert not verify_session_token(None)


def test_admin_lists_created_profiles(admin_client):
    admin_client.post("/profiles", json={"name": "Deck", "buttons": []})
    response = admin_client.get("/admin/profiles")
    assert response.status_code == 200
    assert "Deck" in response.text


def test_admin_create_via_html_form(admin_client):
    response = admin_client.post(
        "/admin/profiles",
        data={"name": "Painel", "locale": "pt_BR", "buttons": "Play|spotify.play"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "Painel" in admin_client.get("/admin/profiles").text


def test_admin_form_rejects_duplicate(admin_client):
    admin_client.post("/profiles", json={"name": "Dup"})
    response = admin_client.post(
        "/admin/profiles", data={"name": "Dup"}, follow_redirects=False
    )
    assert response.status_code == 409
    assert "já existe" in response.text.lower()


def test_admin_delete(admin_client):
    profile_id = admin_client.post("/profiles", json={"name": "Temp"}).json()["id"]
    response = admin_client.post(
        f"/admin/profiles/{profile_id}/delete", follow_redirects=False
    )
    assert response.status_code == 303
    assert admin_client.get(f"/profiles/{profile_id}").status_code == 404


def test_admin_ui_is_localized(admin_client):
    assert "Administração" in admin_client.get("/admin/profiles").text
    english = admin_client.get("/admin/profiles", headers={"Accept-Language": "en"})
    assert "Admin" in english.text


def test_admin_lists_and_revokes_devices(admin_client):
    # The `client` fixture paired device "pytest" (first row on the fresh DB).
    listing = admin_client.get("/admin/devices")
    assert listing.status_code == 200
    assert "pytest" in listing.text
    assert "pair-dev" in listing.text  # pairing code hint

    admin_client.post("/admin/devices/1/revoke")
    assert "Revogado" in admin_client.get("/admin/devices").text


def test_admin_creates_and_deletes_action_binding(admin_client):
    response = admin_client.post(
        "/admin/actions",
        data={"action": "luz.mesa", "executable": "powershell.exe", "args": "-Command 1"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "luz.mesa" in admin_client.get("/admin/actions").text

    admin_client.post("/admin/actions/1/delete")
    assert "luz.mesa" not in admin_client.get("/admin/actions").text


def test_admin_action_form_rejects_duplicate(admin_client):
    admin_client.post("/admin/actions", data={"action": "dup", "executable": "x"})
    response = admin_client.post(
        "/admin/actions",
        data={"action": "dup", "executable": "y"},
        follow_redirects=False,
    )
    assert response.status_code == 409
    assert "já existe" in response.text.lower()


def test_admin_action_form_requires_executable(admin_client):
    response = admin_client.post(
        "/admin/actions",
        data={"action": "sem.exe", "executable": ""},
        follow_redirects=False,
    )
    assert response.status_code == 400


def test_admin_imports_example_bindings(admin_client):
    response = admin_client.post("/admin/actions/examples", follow_redirects=False)
    assert response.status_code == 303
    page = admin_client.get("/admin/actions").text
    assert "notepad.exe" in page
    assert "kitty_portable" in page


def test_admin_example_import_is_idempotent(admin_client):
    admin_client.post("/admin/actions/examples")
    admin_client.post("/admin/actions/examples")
    # Duplicates are skipped, so the key appears exactly once.
    assert admin_client.get("/admin/actions").text.count("bloco.notas") == 1


def test_admin_edits_profile_via_form(admin_client):
    profile_id = admin_client.post(
        "/profiles", json={"name": "Antes", "buttons": []}
    ).json()["id"]

    edit_page = admin_client.get(f"/admin/profiles/{profile_id}/edit")
    assert edit_page.status_code == 200
    assert "Antes" in edit_page.text

    response = admin_client.post(
        f"/admin/profiles/{profile_id}",
        data={
            "name": "Depois",
            "locale": "en",
            "buttons": "Play|spotify.play\nPausa|spotify.pause",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    updated = admin_client.get(f"/profiles/{profile_id}").json()
    assert updated["name"] == "Depois"
    assert updated["locale"] == "en"
    assert [button["action"] for button in updated["buttons"]] == [
        "spotify.play",
        "spotify.pause",
    ]


def test_admin_moves_profile_button_down(admin_client):
    profile_id = admin_client.post(
        "/profiles",
        json={
            "name": "Ordem",
            "buttons": [
                {"index": 0, "label": "A", "action": "a"},
                {"index": 1, "label": "B", "action": "b"},
                {"index": 2, "label": "C", "action": "c"},
            ],
        },
    ).json()["id"]
    buttons = admin_client.get(f"/profiles/{profile_id}").json()["buttons"]
    first = buttons[0]["id"]

    response = admin_client.post(
        f"/admin/profiles/{profile_id}/buttons/{first}/move",
        data={"direction": "down"},
        follow_redirects=False,
    )
    assert response.status_code == 303

    reordered = admin_client.get(f"/profiles/{profile_id}").json()["buttons"]
    assert [button["action"] for button in reordered] == ["b", "a", "c"]


def test_admin_moves_action_in_list(admin_client):
    for key in ("primeira", "segunda", "terceira"):
        admin_client.post(
            "/admin/actions",
            data={"action": key, "executable": "notepad.exe"},
            follow_redirects=False,
        )

    listed = admin_client.get("/admin/actions").text
    assert listed.index("primeira") < listed.index("segunda")
    assert listed.index("segunda") < listed.index("terceira")

    # Move the third action one position up.
    admin_client.post(
        "/admin/actions/3/move", data={"direction": "up"}, follow_redirects=False
    )

    listed = admin_client.get("/admin/actions").text
    assert listed.index("primeira") < listed.index("terceira")
    assert listed.index("terceira") < listed.index("segunda")


def test_admin_edits_action_rebinding_path_and_icon(admin_client, tmp_path):
    created = admin_client.post(
        "/admin/actions",
        data={"action": "luz.mesa", "executable": "powershell.exe", "args": "-Command 1"},
        follow_redirects=False,
    )
    assert created.status_code == 303

    custom = tmp_path / "custom.png"
    custom.write_bytes(PNG_1X1)

    edit_page = admin_client.get("/admin/actions/1/edit")
    assert edit_page.status_code == 200
    assert "powershell.exe" in edit_page.text

    response = admin_client.post(
        "/admin/actions/1",
        data={
            "action": "luz.mesa",
            "executable": "notepad.exe",
            "args": "",
            "icon": str(custom),
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    page = admin_client.get("/admin/actions").text
    assert "notepad.exe" in page
    # The custom icon is served as the deck's icon and in the admin preview.
    preview = admin_client.get("/admin/actions/1/icon")
    assert preview.status_code == 200
    assert preview.content[:8] == PNG_MAGIC
    deck_icon = admin_client.get("/icon", params={"action": "luz.mesa"})
    assert deck_icon.status_code == 200
    assert deck_icon.content[:8] == PNG_MAGIC


def test_admin_missing_custom_icon_answers_404(admin_client):
    admin_client.post(
        "/admin/actions",
        data={
            "action": "sem.icone",
            "executable": "notepad.exe",
            "icon": "C:\\nao\\existe.ico",
        },
        follow_redirects=False,
    )
    # dry-run: no Windows host for .ico extraction -> no icon to serve.
    assert admin_client.get("/admin/actions/1/icon").status_code == 404
    assert admin_client.get("/icon", params={"action": "sem.icone"}).status_code == 404