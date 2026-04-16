"""ui/routes/sessions.py - Session management"""

import json, time
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()
SESSIONS_DIR = Path(__file__).parent.parent.parent / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)


@router.get("/")
async def list_sessions():
    sessions = []
    for f in sorted(SESSIONS_DIR.glob("*.json"), reverse=True):
        try:
            data = json.loads(f.read_text())
            sessions.append({"id": f.stem, "title": data.get("title", f.stem),
                             "created": data.get("created"), "updated": data.get("updated"),
                             "message_count": len(data.get("messages", []))})
        except Exception:
            continue
    return sessions


@router.get("/{session_id}")
async def get_session(session_id: str):
    path = SESSIONS_DIR / f"{session_id}.json"
    if not path.exists():
        return JSONResponse({"error": "Session not found"}, status_code=404)
    return json.loads(path.read_text())


@router.post("/")
async def create_session(body: dict):
    import uuid
    session_id = str(uuid.uuid4())[:8]
    session = {"id": session_id, "title": body.get("title", f"Session {session_id}"),
               "created": time.time(), "updated": time.time(), "messages": []}
    (SESSIONS_DIR / f"{session_id}.json").write_text(json.dumps(session, indent=2))
    return session


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    path = SESSIONS_DIR / f"{session_id}.json"
    if path.exists():
        path.unlink()
    return {"deleted": session_id}
