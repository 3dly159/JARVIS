"""
core/context.py - JARVIS Global Context

Provides context-local storage for tracking session IDs and other metadata
across asynchronous calls and thread boundaries.
"""

from contextvars import ContextVar
from typing import Optional

# The current UI session ID (if spawned from chat)
session_id_ctx: ContextVar[Optional[str]] = ContextVar("session_id", default=None)

# The most recently active session across all interactions (for voice routing)
last_active_session: Optional[str] = None
