def test_pairing_with_valid_code_returns_token(anon_client):
    response = anon_client.post(
        "/pair", json={"code": "pair-dev", "device_name": "deck-android"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "deck-android"
    assert body["device_id"] > 0
    assert len(body["token"]) >= 32


def test_pairing_rejects_bad_code(anon_client):
    response = anon_client.post(
        "/pair", json={"code": "errado", "device_name": "deck"}
    )
    assert response.status_code == 401
    assert "inválido" in response.json()["detail"].lower()


def test_repaired_devices_rotate_token(anon_client):
    first = anon_client.post(
        "/pair", json={"code": "pair-dev", "device_name": "telefone"}
    ).json()["token"]
    second = anon_client.post(
        "/pair", json={"code": "pair-dev", "device_name": "telefone"}
    ).json()["token"]
    assert first != second

    headers = {"Authorization": f"Bearer {first}"}
    assert anon_client.get("/profiles", headers=headers).status_code == 401
    headers = {"Authorization": f"Bearer {second}"}
    assert anon_client.get("/profiles", headers=headers).status_code == 200


def test_protected_routes_require_auth(anon_client):
    assert anon_client.get("/profiles").status_code == 401
    assert anon_client.post("/profiles", json={"name": "x"}).status_code == 401
    assert anon_client.post("/actions", json={"action": "x"}).status_code == 401


def test_revoked_device_token_is_rejected(anon_client):
    body = anon_client.post(
        "/pair", json={"code": "pair-dev", "device_name": "a-ser-revogado"}
    ).json()
    token, device_id = body["token"], body["device_id"]

    assert anon_client.get(
        "/profiles", headers={"Authorization": f"Bearer {token}"}
    ).status_code == 200

    anon_client.post(f"/admin/devices/{device_id}/revoke")
    assert anon_client.get(
        "/profiles", headers={"Authorization": f"Bearer {token}"}
    ).status_code == 401