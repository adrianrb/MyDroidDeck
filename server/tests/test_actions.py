def test_dispatch_action(client):
    response = client.post("/actions", json={"action": "obs.scene", "label": "Cena"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["action"] == "obs.scene"
    assert body["executed_at"]


def test_dispatch_requires_action(client):
    assert client.post("/actions", json={"label": "sem ação"}).status_code == 422
