def test_admin_lists_created_profiles(client):
    client.post("/profiles", json={"name": "Deck", "buttons": []})
    response = client.get("/admin/profiles")
    assert response.status_code == 200
    assert "Deck" in response.text


def test_admin_create_via_html_form(client):
    response = client.post(
        "/admin/profiles",
        data={"name": "Painel", "locale": "pt_BR", "buttons": "Play|spotify.play"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "Painel" in client.get("/admin/profiles").text


def test_admin_form_rejects_duplicate(client):
    client.post("/profiles", json={"name": "Dup"})
    response = client.post(
        "/admin/profiles", data={"name": "Dup"}, follow_redirects=False
    )
    assert response.status_code == 409
    assert "já existe" in response.text.lower()


def test_admin_delete(client):
    profile_id = client.post("/profiles", json={"name": "Temp"}).json()["id"]
    response = client.post(
        f"/admin/profiles/{profile_id}/delete", follow_redirects=False
    )
    assert response.status_code == 303
    assert client.get(f"/profiles/{profile_id}").status_code == 404


def test_admin_ui_is_localized(client):
    assert "Administração" in client.get("/admin/profiles").text
    english = client.get("/admin/profiles", headers={"Accept-Language": "en"})
    assert "Admin" in english.text


def test_admin_lists_and_revokes_devices(client):
    # The `client` fixture paired device "pytest" (first row on the fresh DB).
    listing = client.get("/admin/devices")
    assert listing.status_code == 200
    assert "pytest" in listing.text
    assert "pair-dev" in listing.text  # pairing code hint

    client.post("/admin/devices/1/revoke")
    assert "Revogado" in client.get("/admin/devices").text


def test_admin_creates_and_deletes_action_binding(client):
    response = client.post(
        "/admin/actions",
        data={"action": "luz.mesa", "executable": "powershell.exe", "args": "-Command 1"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "luz.mesa" in client.get("/admin/actions").text

    client.post("/admin/actions/1/delete")
    assert "luz.mesa" not in client.get("/admin/actions").text


def test_admin_action_form_rejects_duplicate(client):
    client.post("/admin/actions", data={"action": "dup", "executable": "x"})
    response = client.post(
        "/admin/actions",
        data={"action": "dup", "executable": "y"},
        follow_redirects=False,
    )
    assert response.status_code == 409
    assert "já existe" in response.text.lower()


def test_admin_action_form_requires_executable(client):
    response = client.post(
        "/admin/actions",
        data={"action": "sem.exe", "executable": ""},
        follow_redirects=False,
    )
    assert response.status_code == 400
