"""
api_server.py - JARVIS API Server (no UI)

FastAPI backend serving only the API endpoints on localhost:8090.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("jarvis.api")

def create_app():
    """Create and configure the FastAPI app with API routes only."""
    app = FastAPI(title="JARVIS API", description="Just A Rather Very Intelligent System API", version="1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register all route modules (API only)
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

    @app.get("/health")
    async def health():
        return {"status": "online", "system": "J.A.R.V.I.S."}

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting API server at http://127.0.0.1:8090")
    uvicorn.run(app, host="127.0.0.1", port=8090, log_level="info")
