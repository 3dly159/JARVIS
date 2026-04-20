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
import mimetypes
import httpx
import subprocess
import os
import signal
import time
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Initialize MIME types for modern web files
mimetypes.init()
mimetypes.add_type('application/javascript', '.tsx')
mimetypes.add_type('application/javascript', '.ts')
mimetypes.add_type('application/javascript', '.jsx')
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('application/javascript', '.mjs')
mimetypes.add_type('text/css', '.css')

logger = logging.getLogger("jarvis.ui")

# Initialize the JARVIS orchestrator if not already initialized
from core.jarvis import jarvis
if not jarvis._initialized:
    jarvis.initialize()

ROOT = Path(__file__).parent.parent
# UI build output - integrated Arc HUD
UI_DIST_DIR = ROOT / "ui_arc"
UI_ASSETS_DIR = UI_DIST_DIR / "dist" / "client" / "assets"


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
    from api.routes import chat, sessions, settings, agents, tasks, memory, system, skills, voice, state, logs, tools, files
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
    app.include_router(logs.router,     prefix="/api/logs",     tags=["logs"])
    app.include_router(tools.router,    prefix="/api/tools",    tags=["tools"])
    app.include_router(files.router,    prefix="/api/files",    tags=["files"])

    @app.middleware("http")
    async def spa_fallback(request: Request, call_next):
        # 1. Bypass for API and health checks
        if request.url.path.startswith("/api") or request.url.path.startswith("/health"):
            return await call_next(request)
        
        # 2. Try proxying to the Node.js SSR Server (port 3000)
        # This is where run-server.js handles TanStack Start SSR.
        try:
            async with httpx.AsyncClient() as client:
                proxy_url = f"http://localhost:3000{request.url.path}"
                if request.query_params:
                    proxy_url += f"?{request.query_params}"
                
                # Check if the SSR server is alive
                proxy_res = await client.request(
                    method=request.method,
                    url=proxy_url,
                    headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
                    content=await request.body() if request.method not in ("GET", "HEAD") else None,
                    timeout=1.0
                )
                
                return Response(
                    content=proxy_res.content,
                    status_code=proxy_res.status_code,
                    headers={k: v for k, v in proxy_res.headers.items() if k.lower() not in ("content-length", "transfer-encoding")}
                )
        except (httpx.ConnectError, httpx.TimeoutException):
            # SSR server is not running or timed out, fall back to API or static assets
            pass

        # 3. Fallback to static serving and SPA routing
        response = await call_next(request)
        
        # 4. If it's a 404 on a non-API route, serve index.html (SPA Fallback)
        if response.status_code == 404:
            # Look for index.html in the UI_DIST_DIR or its dist folder
            # Note: We deleted the manual root index.html, so we look for built one
            index_path = UI_DIST_DIR / "dist" / "client" / "index.html"
            if not index_path.exists():
                index_path = UI_DIST_DIR / "index.html" # Legacy/Template fallback
                
            if index_path.exists():
                return FileResponse(index_path)
                
        return response

    # Mount static files
    if UI_ASSETS_DIR.exists():
        # Relative to index.html, assets are at /dist/client/assets
        app.mount("/dist/client/assets", StaticFiles(directory=str(UI_ASSETS_DIR)), name="assets")
    
    if UI_DIST_DIR.exists():
        app.mount("/", StaticFiles(directory=str(UI_DIST_DIR), html=True), name="static")

    @app.get("/")
    async def read_index():
        return FileResponse(UI_DIST_DIR / "index.html")

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

    async def serve(self):
        """Async start server (non-blocking in current loop)."""
        import uvicorn
        logger.info(f"UI server starting at http://{self.host}:{self.port}")
        config = uvicorn.Config(app, host=self.host, port=self.port, log_level="warning")
        self._server = uvicorn.Server(config)
        await self._server.serve()

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