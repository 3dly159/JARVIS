"""
core/brain.py - JARVIS Brain (LLM Interface)
Wraps OpenAI-compatible endpoint (NVIDIA Nemotron) with streaming, tool-calling, and MCU-style personality.
"""

import json
import logging
import os
from datetime import datetime
from typing import Generator, Optional, Callable

from openai import OpenAI

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# Default values; will be overridden from config.yaml if present
DEFAULT_MODEL = "nvidia/nemotron-3-super-120b-a12b"
DEFAULT_TEMPERATURE = 1.0
DEFAULT_TOP_P = 0.95
DEFAULT_MAX_TOKENS = 8192
DEFAULT_ENABLE_THINKING = False
DEFAULT_REASONING_BUDGET = 16384
# Context window for trimming history (approximate)
CONTEXT_WINDOW = 16384

logger = logging.getLogger("jarvis.brain")


def get_system_prompt() -> str:
    """Returns the dynamic system prompt assembled from JARVIS identity files."""
    from core.context_loader import context_loader
    return context_loader.load()


def _build_tools_prompt() -> str:
    """Build tool usage instructions for the system prompt."""
    try:
        from tools.registry import registry
        tools = registry.get_all()
        if not tools:
            return ""
        lines = [
            "\n\n## Tool Usage",
            "When you need to use a tool, respond with ONLY this JSON format (no other text):",
            '{"tool": "tool_name", "params": {"param": "value"}}',
            "After receiving a tool result, continue your response naturally.",
            "\nAvailable tools:",
        ]
        for t in tools:
            params = ", ".join(f"{k}: {v}" for k, v in t["params"].items())
            lines.append(f"  - {t['name']}({params}): {t['description']}")
        return "\n".join(lines)
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Tool Registry (populated by tools/registry.py at runtime)
# ---------------------------------------------------------------------------

_registered_tools: dict[str, dict] = {}


def register_tool(name: str, schema: dict, handler: Callable):
    """Register a tool the brain can call."""
    _registered_tools[name] = {"schema": schema, "handler": handler}
    logger.debug(f"Tool registered: {name}")


def get_tool_schemas() -> list[dict]:
    """Returns all tool schemas for injection into prompts."""
    return [v["schema"] for v in _registered_tools.values()]


# ---------------------------------------------------------------------------
# Conversation History
# ---------------------------------------------------------------------------

class ConversationHistory:
    """Manages a rolling conversation history within the context window."""

    def __init__(self, max_tokens: int = CONTEXT_WINDOW):
        self.messages: list[dict] = []
        self.max_tokens = max_tokens

    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        self._trim()

    def _trim(self):
        """Rough trim: drop oldest non-system messages if history gets long."""
        # Estimate ~4 chars per token
        total_chars = sum(len(m["content"]) for m in self.messages)
        while total_chars > self.max_tokens * 4 and len(self.messages) > 2:
            removed = self.messages.pop(0)
            total_chars -= len(removed["content"])

    def get(self) -> list[dict]:
        return self.messages.copy()

    def clear(self):
        self.messages.clear()


# ---------------------------------------------------------------------------
# Brain Class
# ---------------------------------------------------------------------------

class Brain:
    """
    Core LLM interface for JARVIS.
    Handles streaming responses, tool calls, and conversation history.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        enable_thinking: Optional[bool] = None,
        reasoning_budget: Optional[int] = None,
        on_token: Optional[Callable[[str], None]] = None,
    ):
        from core.config_manager import config as cfg

        # Load config values with fallbacks
        self.model = model or cfg.get("nvidia.model") or DEFAULT_MODEL
        self.temperature = temperature if temperature is not None else cfg.get("nvidia.temperature", DEFAULT_TEMPERATURE)
        self.top_p = top_p if top_p is not None else cfg.get("nvidia.top_p", DEFAULT_TOP_P)
        self.max_tokens = max_tokens if max_tokens is not None else cfg.get("nvidia.max_tokens", DEFAULT_MAX_TOKENS)
        self.enable_thinking = (
            enable_thinking if enable_thinking is not None else cfg.get("nvidia.enable_thinking", DEFAULT_ENABLE_THINKING)
        )
        self.reasoning_budget = (
            reasoning_budget
            if reasoning_budget is not None
            else cfg.get("nvidia.reasoning_budget", DEFAULT_REASONING_BUDGET)
        )
        self.on_token = on_token  # callback called with each streamed token
        self.history = ConversationHistory()

        # Build OpenAI-compatible client
        api_key = cfg.get("nvidia.api_key") or os.getenv("NVIDIA_API_KEY")
        base_url = cfg.get("nvidia.base_url") or os.getenv("NVIDIA_BASE_URL") or "https://integrate.api.nvidia.com/v1"
        if not api_key:
            logger.warning(
                "NVIDIA API key not found. Set `nvidia.api_key` in config.yaml or export NVIDIA_API_KEY environment variable."
            )
        self.client = OpenAI(base_url=base_url, api_key=api_key) if api_key else None

        logger.info(
            f"Brain online. Model: {self.model}, temperature: {self.temperature}, top_p: {self.top_p}, "
            f"max_tokens: {self.max_tokens}, enable_thinking: {self.enable_thinking}, reasoning_budget: {self.reasoning_budget}"
        )

    # ----- Core: stream a response -----

    def _stream(self, messages: list[dict]) -> Generator[str, None, None]:
        """
        Sends messages to the OpenAI-compatible endpoint and yields tokens as they arrive.
        """
        if self.client is None:
            yield "[ERROR] NVIDIA client not initialized (missing API key)."
            return

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_tokens,
                extra_body={
                    "chat_template_kwargs": {"enable_thinking": self.enable_thinking},
                    "reasoning_budget": self.reasoning_budget,
                },
                timeout=120,
            )
        except Exception as e:
            logger.error(f"Failed to start NVIDIA chat stream: {e}")
            yield f"[ERROR] Unable to contact NVIDIA endpoint: {e}"
            return

        for chunk in response:
            try:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if getattr(delta, "content", None):
                    token = delta.content
                    if token:
                        yield token
                        if self.on_token:
                            self.on_token(token)
            except Exception as e:
                logger.debug(f"Error parsing chunk: {e}")
                continue

    # ----- Public: think (single prompt, no history) -----

    def think(self, prompt: str, system: Optional[str] = None) -> str:
        """
        One-shot prompt — no conversation history.
        Used internally (task tracker, self-mod, agents).
        Returns full response string.
        """
        messages = [
            {"role": "system", "content": system or get_system_prompt()},
            {"role": "user", "content": prompt},
        ]
        response = ""
        for token in self._stream(messages):
            response += token
        return response.strip()

    # ----- Public: chat (conversational, with history + tool-calling loop) -----

    def chat(self, user_message: str) -> Generator[str, None, None]:
        """
        Conversational interface — maintains history.
        Yields tokens for streaming to UI/voice.
        Handles tool calls automatically in a loop.
        """
        self.history.add("user", user_message)

        system = get_system_prompt() + _build_tools_prompt()
        messages = [
            {"role": "system", "content": system},
            *self.history.get(),
        ]

        full_response = ""
        for token in self._stream(messages):
            full_response += token
            if self.on_token:
                self.on_token(token)
            yield token

        full_response = full_response.strip()

        # Tool-calling loop
        tool_result = self._try_tool_call(full_response)
        if tool_result is not None:
            # Inject tool result and get follow-up response
            self.history.add("assistant", full_response)
            self.history.add("user", f"[Tool result]: {tool_result}")
            messages2 = [
                {"role": "system", "content": system},
                *self.history.get(),
            ]
            follow_up = ""
            for token in self._stream(messages2):
                follow_up += token
                if self.on_token:
                    self.on_token(token)
                yield token
            self.history.add("assistant", follow_up.strip())
        else:
            self.history.add("assistant", full_response)

    # ----- Public: chat_full (non-streaming, returns complete string) -----

    def chat_full(self, user_message: str) -> str:
        """
        Conversational interface — returns full response string (non-streaming).
        """
        return "".join(self.chat(user_message))

    # ----- Context injection -----

    def _try_tool_call(self, response: str):
        """Check if response is a tool call JSON. Execute it and return result or None."""
        import json, re
        try:
            # Extract JSON from response (handles markdown code blocks too)
            match = re.search(r'\{\s*"tool"\s*:', response)
            if not match:
                return None
            json_str = response[match.start():]
            # Find balanced closing brace
            depth, end = 0, -1
            for i, c in enumerate(json_str):
                if c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                if depth == 0:
                    end = i + 1
                    break
            if end == -1:
                return None
            call = json.loads(json_str[:end])
            tool_name = call.get("tool")
            params = call.get("params", {})
            if not tool_name:
                return None
            from tools.registry import registry
            result = registry.call(tool_name, **params)
            logger.info(f"Tool call: {tool_name}({params}) -> {str(result)[:80]}")
            return result
        except Exception as e:
            logger.debug(f"Tool call parse failed: {e}")
            return None

    def inject_context(self, context: str):
        """
        Injects a system-level context message into history.
        Used by memory, task tracker, etc. to give JARVIS background info.
        """
        self.history.add(
            "system",
            f"[Context update — {datetime.now().strftime('%H:%M')}]\n{context}",
        )

    def clear_history(self):
        """Clears conversation history (new session)."""
        self.history.clear()
        logger.info("Conversation history cleared.")

    # ----- Introspection -----

    def status(self) -> dict:
        return {
            "model": self.model,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "enable_thinking": self.enable_thinking,
            "reasoning_budget": self.reasoning_budget,
            "history_length": len(self.history.messages),
            "tools_registered": list(_registered_tools.keys()),
        }


# ---------------------------------------------------------------------------
# Singleton instance (imported by other modules)
# ---------------------------------------------------------------------------

brain = Brain()


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Testing JARVIS brain...\n")
    print("JARVIS: ", end="", flush=True)
    for token in brain.chat("Introduce yourself briefly."):
        print(token, end="", flush=True)
    print("\n")
    print("Status:", brain.status())