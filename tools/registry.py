"""
tools/registry.py - JARVIS Tool Registry

Auto-discovers tools and exposes them to the brain.
Brain picks tools via function-calling style prompting.

Usage:
    from tools.registry import registry
    registry.register("web_search", schema, handler)
    tools = registry.get_all()
    result = registry.call("web_search", query="python news")
"""

import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("jarvis.tools")


class ToolRegistry:
    """
    Central tool registry. All tools register here.
    Brain gets tool schemas to decide which to call.
    """

    def __init__(self):
        self._tools: dict[str, dict] = {}

    def register(self, name: str, description: str, handler: Callable = None, params: dict = None):
        """
        Register a tool. Can be used as a standard call or a decorator.
        name: unique tool name
        description: what it does (used in brain prompt)
        handler: callable(**kwargs) → result string
        params: dict of param_name → description
        """
        def decorator(func: Callable):
            self._tools[name] = {
                "name": name,
                "description": description,
                "handler": func,
                "params": params or {},
            }
            logger.debug(f"Tool registered: {name}")
            return func

        if handler is None:
            return decorator
        return decorator(handler)

    def call(self, tool_name: str, **kwargs) -> str:
        """Call a tool by name with kwargs. Returns result string."""
        if tool_name not in self._tools:
            logger.warning(f"Tool not found: {tool_name}")
            return f"Error: tool '{tool_name}' not found."
        try:
            result = self._tools[tool_name]["handler"](**kwargs)
            logger.info(f"Tool '{tool_name}' called → {str(result)[:80]}")
            return str(result)
        except Exception as e:
            logger.error(f"Tool '{tool_name}' error: {e}")
            return f"Error running {tool_name}: {e}"

    def get_all(self) -> list[dict]:
        """Get all tool schemas (for brain prompt injection)."""
        return [
            {"name": t["name"], "description": t["description"], "params": t["params"]}
            for t in self._tools.values()
        ]

    def get_prompt_block(self) -> str:
        """Format tool list as a prompt block for the brain."""
        if not self._tools:
            return "No tools available."
        lines = ["Available tools (call by name):"]
        for t in self._tools.values():
            params = ", ".join(f"{k}: {v}" for k, v in t["params"].items())
            lines.append(f"  - {t['name']}({params}): {t['description']}")
        return "\n".join(lines)

    def list_names(self) -> list[str]:
        return list(self._tools.keys())

    def status(self) -> dict:
        return {"registered_tools": self.list_names()}


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

registry = ToolRegistry()
