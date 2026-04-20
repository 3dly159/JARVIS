"""ui/routes/chat.py - Chat + streaming WebSocket"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import logging, json, time, asyncio
from pathlib import Path
from core.context import session_id_ctx
import core.context as ctx

router = APIRouter()
logger = logging.getLogger("jarvis.ui.chat")
SESSIONS_DIR = Path(__file__).parent.parent.parent / "sessions"

def save_session_message(session_id: str, role: str, content: str, parts: list = None):
    """Helper to persist messages to session file, including structured parts if available."""
    path = SESSIONS_DIR / f"{session_id}.json"
    session = {"id": session_id, "title": f"Session {session_id}", "created": time.time(), "updated": time.time(), "messages": []}
    if path.exists():
        try:
            session = json.loads(path.read_text())
        except Exception:
            pass
    
    msg = {"role": role, "content": content, "timestamp": time.time()}
    if parts:
        msg["parts"] = parts
        
    session["messages"].append(msg)
    session["updated"] = time.time()
    
    # Simple title generation from first message
    if len(session["messages"]) == 1 and role == "user":
        session["title"] = content[:30] + ("..." if len(content) > 30 else "")
        
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(session, indent=2))


@router.post("")
async def chat(body: dict):
    """Non-streaming chat endpoint."""
    message = body.get("message", "").strip()
    session_id = body.get("session_id", "default")
    if not message:
        return JSONResponse({"error": "Empty message"}, status_code=400)
    try:
        ctx.last_active_session = session_id
        save_session_message(session_id, "user", message)
        from core.jarvis import jarvis
        response = await jarvis.chat(message)
        # Note: In non-streaming, we don't handle parts yet for simplicity
        save_session_message(session_id, "jarvis", response)
        return {"response": response, "session_id": session_id}
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


# ---------------------------------------------------------------------------
# Broadcaster for Async Updates
# ---------------------------------------------------------------------------

class ChatBroadcaster:
    """Manages active WebSockets for real-time mission reporting."""
    def __init__(self):
        self.connections: dict[str, list[WebSocket]] = {}
        self.lock = asyncio.Lock()

    async def register(self, session_id: str, websocket: WebSocket):
        async with self.lock:
            if session_id not in self.connections:
                self.connections[session_id] = []
            self.connections[session_id].append(websocket)
            logger.debug(f"Broadcaster: Session {session_id} registered.")

    async def unregister(self, session_id: str, websocket: WebSocket):
        async with self.lock:
            if session_id in self.connections:
                try:
                    self.connections[session_id].remove(websocket)
                    if not self.connections[session_id]:
                        del self.connections[session_id]
                    logger.debug(f"Broadcaster: Session {session_id} unregistered.")
                except ValueError:
                    pass

    async def send(self, session_id: str, payload: dict):
        """Send a message to all WebSockets active for this session."""
        async with self.lock:
            sockets = self.connections.get(session_id, [])
            if not sockets:
                logger.debug(f"Broadcaster: No active sockets for session {session_id}")
                return

            # Prepare message
            msg = json.dumps(payload)
            
            # Fan-out
            tasks = []
            for ws in sockets:
                tasks.append(ws.send_text(msg))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

chat_broadcaster = ChatBroadcaster()


@router.websocket("/ws")
async def chat_ws(websocket: WebSocket):
    """Streaming chat via WebSocket. Client sends JSON {message, session_id}."""
    await websocket.accept()
    logger.info("Chat WebSocket connected.")
    current_session = websocket.query_params.get("session_id", "default")
    await chat_broadcaster.register(current_session, websocket)
    ctx.last_active_session = current_session
    logger.info(f"Chat WebSocket connected (Session: {current_session})")
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                message = payload.get("message", "").strip()
                session_id = payload.get("session_id", "default")
            except Exception:
                message = data.strip()
                session_id = "default"

            if session_id != current_session:
                await chat_broadcaster.unregister(current_session, websocket)
                current_session = session_id
                await chat_broadcaster.register(session_id, websocket)
                ctx.last_active_session = session_id

            if not message:
                continue

            # Set context for this specific message chain
            token = session_id_ctx.set(session_id)
            
            save_session_message(session_id, "user", message)

            try:
                from core.jarvis import jarvis
                full_conversation_text = ""
                all_segments = []
                
                async for segment in jarvis.chat_stream(message):
                    # Relay the raw segment (contains type, content/metadata)
                    await websocket.send_text(json.dumps({"segment": segment, "done": False}))
                    
                    all_segments.append(segment)
                    if segment["type"] == "text":
                        full_conversation_text += segment["content"]
                
                # Convert backend segments to frontend parts format
                # backend: {type: text, content: ...} | {type: tool_call, tool: ..., params: ...}
                # frontend: {type: text, text: ...} | {type: tool_call, tool: ..., params: ...}
                parts = []
                current_text = ""
                for s in all_segments:
                    if s["type"] == "text":
                        current_text += s["content"]
                    else:
                        if current_text:
                            parts.append({"type": "text", "text": current_text})
                            current_text = ""
                        parts.append(s) # tool_call and tool_result already match types
                if current_text:
                    parts.append({"type": "text", "text": current_text})

                save_session_message(session_id, "jarvis", full_conversation_text, parts=parts)
                await websocket.send_text(json.dumps({"segment": None, "done": True}))
            except Exception as e:
                logger.error(f"WS Chat error: {e}")
                await websocket.send_text(json.dumps({"error": str(e), "done": True}))

    except WebSocketDisconnect:
        logger.info("Chat WebSocket disconnected.")
    finally:
        await chat_broadcaster.unregister(current_session, websocket)
