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
