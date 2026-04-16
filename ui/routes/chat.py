"""ui/routes/chat.py - Chat + streaming WebSocket"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import logging, json

router = APIRouter()
logger = logging.getLogger("jarvis.ui.chat")


@router.post("/")
async def chat(body: dict):
    """Non-streaming chat endpoint."""
    message = body.get("message", "").strip()
    session_id = body.get("session_id", "default")
    if not message:
        return JSONResponse({"error": "Empty message"}, status_code=400)
    try:
        from core.jarvis import jarvis
        response = jarvis.chat(message)
        return {"response": response, "session_id": session_id}
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@router.websocket("/ws")
async def chat_ws(websocket: WebSocket):
    """Streaming chat via WebSocket. Client sends JSON {message, session_id}."""
    await websocket.accept()
    logger.info("Chat WebSocket connected.")
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                message = payload.get("message", "").strip()
            except Exception:
                message = data.strip()

            if not message:
                continue

            try:
                from core.jarvis import jarvis
                for token in jarvis.chat_stream(message):
                    await websocket.send_text(json.dumps({"token": token, "done": False}))
                await websocket.send_text(json.dumps({"token": "", "done": True}))
            except Exception as e:
                await websocket.send_text(json.dumps({"error": str(e), "done": True}))

    except WebSocketDisconnect:
        logger.info("Chat WebSocket disconnected.")
