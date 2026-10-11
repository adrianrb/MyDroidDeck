from app.core.config import settings


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