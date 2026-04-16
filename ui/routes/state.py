"""
ui/routes/state.py - JARVIS State Broadcaster

WebSocket that broadcasts JARVIS state changes to all connected UI clients.
Orb, status bar, and any other UI component subscribes here.

States: standby | listening | thinking | speaking
"""

import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
logger = logging.getLogger("jarvis.ui.state")

# All connected WebSocket clients
_clients: list[WebSocket] = []
_current_state: str = "standby"


async def broadcast(state: str, extra: dict = None):
    """Broadcast a state change to all connected clients."""
    global _current_state
    _current_state = state
    msg = {"state": state, **(extra or {})}
    dead = []
    for ws in _clients:
        try:
            await ws.send_json(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _clients.remove(ws)


def set_state_sync(state: str, extra: dict = None):
    """
    Synchronous wrapper — call from non-async JARVIS modules.
    e.g. set_state_sync("thinking") when brain starts processing.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(broadcast(state, extra))
        else:
            loop.run_until_complete(broadcast(state, extra))
    except Exception as e:
        logger.debug(f"State broadcast error: {e}")


@router.websocket("/ws")
async def state_ws(websocket: WebSocket):
    """Clients connect here to receive live state updates."""
    await websocket.accept()
    _clients.append(websocket)
    # Send current state immediately on connect
    await websocket.send_json({"state": _current_state})
    try:
        while True:
            # Keep alive — clients can send pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        _clients.remove(websocket) if websocket in _clients else None


@router.get("/")
async def get_state():
    return {"state": _current_state, "clients": len(_clients)}
