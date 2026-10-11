import re

from app import __version__


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == __version__


def test_version_is_semver(client):
    response = client.get("/version")
    assert response.status_code == 200
    assert re.fullmatch(r"\d+\.\d+\.\d+", response.json()["version"])


def test_health_message_defaults_to_pt_br(client):
    assert client.get("/health").json()["message"] == "Operacional"


def test_health_message_english(client):
    response = client.get("/health", headers={"Accept-Language": "en-US,en;q=0.9"})
    assert response.json()["message"] == "Healthy"
