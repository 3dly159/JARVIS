"""
ui/server.py - JARVIS Web UI Server

FastAPI backend serving the JARVIS dashboard on localhost:8080.
All routes pull live values from config_manager — nothing hardcoded.
WebSocket for streaming chat responses.

Run standalone: uvicorn ui.server:app --host 127.0.0.1 --port 8080
Or via main.py: jarvis.ui.run()
"""

import logging
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger("jarvis.ui")

ROOT = Path(__file__).parent.parent
STATIC_DIR = Path(__file__).parent / "static"


def create_app():
    """Create and configure the FastAPI app with all routes."""
    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(title="JARVIS", description="Just A Rather Very Intelligent System", version="1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Register all route modules
    from ui.routes import chat, sessions, settings, agents, tasks, memory, system, skills
    app.include_router(chat.router,     prefix="/api/chat",     tags=["chat"])
    app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
    app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
    app.include_router(agents.router,   prefix="/api/agents",   tags=["agents"])
    app.include_router(tasks.router,    prefix="/api/tasks",    tags=["tasks"])
    app.include_router(memory.router,   prefix="/api/memory",   tags=["memory"])
    app.include_router(system.router,   prefix="/api/system",   tags=["system"])
    app.include_router(skills.router,   prefix="/api/skills",   tags=["skills"])

    # Serve main UI
    @app.get("/")
    async def index():
        from fastapi.responses import FileResponse
        index_path = STATIC_DIR / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return {"status": "JARVIS UI — place index.html in ui/static/"}

    @app.get("/health")
    async def health():
        return {"status": "online", "system": "J.A.R.V.I.S."}

    return app


app = create_app()


class UIServer:
    """Wraps uvicorn for programmatic start/stop."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8080):
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
