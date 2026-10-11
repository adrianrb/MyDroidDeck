import pytest
from starlette.websockets import WebSocketDisconnect


def test_socket_requires_valid_token(client):
    with client.websocket_connect("/ws/deck?token=wrong") as websocket:
        assert websocket.receive_json()["type"] == "error"
        with pytest.raises(WebSocketDisconnect):
            websocket.receive_json()


def test_socket_welcomes_and_acknowledges(client):
    with client.websocket_connect("/ws/deck?token=dev-token") as websocket:
        welcome = websocket.receive_json()
        assert welcome["type"] == "welcome"
        websocket.send_json({"action": "obs.scene"})
        assert websocket.receive_json() == {"type": "ack", "action": "obs.scene"}
