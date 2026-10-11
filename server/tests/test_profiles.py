def _payload(name="Deck principal"):
    return {
        "name": name,
        "locale": "pt_BR",
        "buttons": [
            {"index": 0, "label": "Cena inicial", "action": "obs.scene.iniciar"},
            {"index": 1, "label": "Play", "action": "spotify.play"},
        ],
    }


def test_create_and_get_profile_round_trips_utf8(client):
    created = client.post("/profiles", json=_payload())
    assert created.status_code == 201
    profile = created.json()
    assert profile["name"] == "Deck principal"
    assert profile["buttons"][0]["label"] == "Cena inicial"

    fetched = client.get(f"/profiles/{profile['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["buttons"][0]["label"] == "Cena inicial"


def test_duplicate_name_is_conflict(client):
    assert client.post("/profiles", json=_payload()).status_code == 201
    duplicate = client.post("/profiles", json=_payload())
    assert duplicate.status_code == 409
    assert "perfil" in duplicate.json()["detail"].lower()


def test_missing_profile_is_404_localized(client):
    default = client.get("/profiles/9999")
    assert default.status_code == 404
    assert "não encontrado" in default.json()["detail"].lower()

    english = client.get("/profiles/9999", headers={"Accept-Language": "en"})
    assert "not found" in english.json()["detail"].lower()


def test_delete_profile(client):
    profile_id = client.post("/profiles", json=_payload()).json()["id"]
    assert client.delete(f"/profiles/{profile_id}").status_code == 204
    assert client.get(f"/profiles/{profile_id}").status_code == 404


def _example_actions(admin_client):
    """Seed the standard bindings and return a fresh empty profile id."""
    admin_client.post("/admin/actions/examples", follow_redirects=False)
    return admin_client.post(
        "/profiles", json={"name": "deck padrao", "locale": "pt_BR", "buttons": []}
    ).json()["id"]


def test_fill_profile_with_standard_actions(admin_client):
    profile_id = _example_actions(admin_client)

    filled = admin_client.post(
        f"/admin/profiles/{profile_id}/examples", follow_redirects=False
    )
    assert filled.status_code == 303

    buttons = admin_client.get(f"/profiles/{profile_id}").json()["buttons"]
    assert [button["action"] for button in buttons] == [
        "bloco.notas",
        "calculadora",
        "paint",
        "explorer",
        "gerenciador.tarefas",
        "kitty",
        "obs.gravar",
        "script.exemplo",
    ]
    assert [button["index"] for button in buttons] == list(range(8))
    assert buttons[0]["label"] == "bloco.notas"


def test_fill_profile_is_idempotent_and_keeps_existing_buttons(admin_client):
    admin_client.post("/admin/actions/examples", follow_redirects=False)
    # The owner's own buttons must survive the fill.
    profile_id = admin_client.post("/profiles", json=_payload()).json()["id"]

    for _ in range(2):
        admin_client.post(
            f"/admin/profiles/{profile_id}/examples", follow_redirects=False
        )

    buttons = admin_client.get(f"/profiles/{profile_id}").json()["buttons"]
    assert buttons[0]["label"] == "Cena inicial"
    assert buttons[1]["label"] == "Play"
    # 2 own + 8 standard, no duplicates, sequential indexes.
    assert len(buttons) == 10
    assert len({button["action"] for button in buttons}) == 10
    assert [button["index"] for button in buttons] == list(range(10))


def test_fill_missing_profile_is_a_noop(admin_client):
    response = admin_client.post("/admin/profiles/9999/examples", follow_redirects=False)
    assert response.status_code == 303
