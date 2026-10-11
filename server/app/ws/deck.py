"""Deck control WebSocket.

The app connects to ``/ws/deck?token=<ws_token>``. Real command dispatch (OBS,
shell, etc.) is added later; for now the server welcomes and acknowledges.
"""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app import __version__
from app.core.config import settings

router = APIRouter()


@router.websocket("/ws/deck")
async def deck_socket(websocket: WebSocket) -> None:
    await websocket.accept()

    if websocket.query_params.get("token") != settings.ws_token:
        await websocket.send_json({"type": "error", "code": "unauthorized"})
        await websocket.close(code=4401)
        return

    await websocket.send_json({"type": "welcome", "version": __version__})
    try:
        while True:
            message = await websocket.receive_json()
            await websocket.send_json(
                {"type": "ack", "action": message.get("action")}
            )
    except WebSocketDisconnect:
        return
