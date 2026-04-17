"""
api_server.py - Pure API server for JARVIS (no UI serving)
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import chat, sessions, settings, agents, tasks, memory, system, skills, voice, state

def create_app():
    app = FastAPI(title="JARVIS API", description="Just A Rather Very Intelligent System", version="1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register all API route modules
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
