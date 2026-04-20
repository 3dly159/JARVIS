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
_current_state: str = "idle"


_loop: asyncio.AbstractEventLoop = None

async def broadcast(state: str, extra: dict = None):
    """Broadcast a state change to all connected clients."""
    global _current_state, _loop
    # Capture the loop if we don't have it yet
    if not _loop:
        try:
            _loop = asyncio.get_running_loop()
        except RuntimeError:
            pass

    _current_state = state
    msg = {"type": "state", "orbState": state, **(extra or {})}
    dead = []
    for ws in _clients:
        try:
            await ws.send_json(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in _clients:
            _clients.remove(ws)


def set_state_sync(state: str, extra: dict = None):
    """
    Thread-safe synchronous wrapper.
    """
    global _loop
    
    # Use the captured UI loop if available
    target_loop = _loop
    
    # Fallback to jarvis.loop if state was triggered before first UI connection
    if not target_loop:
        try:
            from core.jarvis import jarvis
            target_loop = jarvis.loop
        except Exception:
            pass

    if target_loop and target_loop.is_running():
        target_loop.call_soon_threadsafe(
            lambda: asyncio.create_task(broadcast(state, extra))
        )
    else:
        # Ultimate fallback: try to find any loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(broadcast(state, extra))
        except Exception:
            pass


@router.websocket("/ws")
async def state_ws(websocket: WebSocket):
    """Clients connect here to receive live state updates."""
    await websocket.accept()
    _clients.append(websocket)
    # Send current state immediately on connect
    await websocket.send_json({"type": "state", "orbState": _current_state})
    try:
        while True:
            # Keep alive — clients can send pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        _clients.remove(websocket) if websocket in _clients else None


@router.get("/")
async def get_state():
    return {"state": _current_state, "clients": len(_clients)}
