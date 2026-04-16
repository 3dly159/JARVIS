"""
core/brain.py - JARVIS Brain (LLM Interface)
Wraps Ollama + Mistral 7B with streaming, tool-calling, and MCU-style personality.
"""

import json
import logging
import requests
from datetime import datetime
from typing import Generator, Optional, Callable

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

OLLAMA_HOST = "http://localhost:11434"
DEFAULT_MODEL = "mistral:7b-instruct-q4_K_M"
CONTEXT_WINDOW = 8192
TEMPERATURE = 0.7

logger = logging.getLogger("jarvis.brain")


def get_system_prompt() -> str:
    """Returns the dynamic system prompt assembled from JARVIS identity files."""
    from core.context_loader import context_loader
    return context_loader.load()


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
        model: str = DEFAULT_MODEL,
        ollama_host: str = OLLAMA_HOST,
        temperature: float = TEMPERATURE,
        on_token: Optional[Callable[[str], None]] = None,
    ):
        self.model = model
        self.ollama_host = ollama_host
        self.temperature = temperature
        self.on_token = on_token  # callback called with each streamed token
        self.history = ConversationHistory()
        self._check_ollama()

    # ----- Ollama health check -----

    def _check_ollama(self):
        try:
            r = requests.get(f"{self.ollama_host}/api/tags", timeout=3)
            r.raise_for_status()
            models = [m["name"] for m in r.json().get("models", [])]
            if self.model not in models:
                logger.warning(
                    f"Model '{self.model}' not found in Ollama. "
                    f"Available: {models}. Run: ollama pull {self.model}"
                )
            else:
                logger.info(f"Brain online. Model: {self.model}")
        except requests.exceptions.ConnectionError:
            logger.error(
                "Cannot reach Ollama at %s — is it running?", self.ollama_host
            )
        except Exception as e:
            logger.error("Ollama health check failed: %s", e)

    # ----- Core: stream a response -----

    def _stream(self, messages: list[dict]) -> Generator[str, None, None]:
        """
        Sends messages to Ollama and yields tokens as they arrive.
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": self.temperature,
                "num_ctx": CONTEXT_WINDOW,
            },
        }

        try:
            with requests.post(
                f"{self.ollama_host}/api/chat",
                json=payload,
                stream=True,
                timeout=120,
            ) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        token = chunk.get("message", {}).get("content", "")
                        if token:
                            yield token
                        if chunk.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue
        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out.")
            yield "\n[JARVIS: response timed out]"
        except Exception as e:
            logger.error("Stream error: %s", e)
            yield f"\n[JARVIS: error — {e}]"

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
            if self.on_token:
                self.on_token(token)
        return response.strip()

    # ----- Public: chat (conversational, with history) -----

    def chat(self, user_message: str) -> Generator[str, None, None]:
        """
        Conversational interface — maintains history.
        Yields tokens for streaming to UI/voice.
        Automatically appends to history when done.
        """
        self.history.add("user", user_message)

        messages = [
            {"role": "system", "content": get_system_prompt()},
            *self.history.get(),
        ]

        full_response = ""
        for token in self._stream(messages):
            full_response += token
            if self.on_token:
                self.on_token(token)
            yield token

        self.history.add("assistant", full_response.strip())

    # ----- Public: chat_full (non-streaming, returns complete string) -----

    def chat_full(self, user_message: str) -> str:
        """
        Conversational interface — returns full response string (non-streaming).
        """
        return "".join(self.chat(user_message))

    # ----- Context injection -----

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
            "ollama_host": self.ollama_host,
            "temperature": self.temperature,
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
