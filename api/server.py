"""
ui/server.py - JARVIS Web UI Server

FastAPI backend serving the JARVIS dashboard on localhost:8090.
All routes pull live values from config_manager — nothing hardcoded.
WebSocket for streaming chat responses.

Run standalone: uvicorn ui.server:app --host 127.0.0.1 --port 8090
Or via main.py: jarvis.ui.run()
"""

import logging
import threading
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("jarvis.ui")

ROOT = Path(__file__).parent.parent
# UI build output - using orb UI now
ORB_UI_DIR = ROOT / "ui_orb"
STATIC_DIR = ROOT / "ui" / "dist"  # Keep for fallback


def create_app():
    """Create and configure the FastAPI app with all routes."""
    app = FastAPI(title="JARVIS", description="Just A Rather Very Intelligent System", version="1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register all API route modules under /api/
    from api.routes import chat, sessions, settings, agents, tasks, memory, system, skills, voice, state
    app.include_router(chat.router,     prefix="/api/chat",     tags=["chat"])
    app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
    app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
    app.include_router(agents.router,   prefix="/api/agents",   tags=["agents"])
    app.include_router(tasks.router,    prefix="/api/tasks",    tags=["tasks"])
    app.include_router(memory.router,   prefix="/api/memory",   tags=["memory"])
    app.include_router(system.router,   prefix="/api/system",   tags=["system"])
    app.include_router(skills.router,   prefix="/api/skills",   tags=["skills"])
    app.include_router(voice.router,    prefix="/api/voice",    tags=["voice"])
    app.include_router(state.router,    prefix="/api/state",    tags=["state"])

    # Middleware for SPA fallback: if request is not for /api/ and the requested file does not exist,
    # serve index.html (single-page app).
    @app.middleware("http")
    async def spa_fallback(request: Request, call_next):
        if request.url.path.startswith("/api"):
            return await call_next(request)
        # Check if file exists in static directory
        rel_path = request.url.path.lstrip("/")
        if rel_path == "":
            rel_path = "index.html"
        file_path = STATIC_DIR / rel_path
        if file_path.is_file():
            return await call_next(request)
        else:
            # Serve index.html
            index_path = STATIC_DIR / "index.html"
            return FileResponse(index_path)

    # Mount static files to serve assets, index.html, etc.
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/health")
    async def health():
        return {"status": "online", "system": "J.A.R.V.I.S."}

    return app


app = create_app()


class UIServer:
    """Wraps uvicorn for programmatic start/stop."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8090):
        self.host = host
        self.port = port
        self._server = None
        self._thread: Optional[threading.Thread] = None

    def run(self):
        """Start server (blocking)."""
        import uvicorn
        logger.info(f"UI server starting at http://{self.host}:{self.port}")
        uvicorn.run(app, host=self.host, port=self.port, log_level="warning")

    def start_background(self):
        """Start server in background thread."""
        self._thread = threading.Thread(target=self.run, daemon=True, name="ui-server")
        self._thread.start()
        logger.info(f"UI server started in background: http://{self.host}:{self.port}")

    def stop(self):
        if self._server:
            self._server.should_exit = True

