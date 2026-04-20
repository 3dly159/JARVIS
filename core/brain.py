"""
core/brain.py - JARVIS Brain (LLM Interface)
Wraps OpenAI-compatible endpoint (NVIDIA Nemotron) with streaming, tool-calling, and MCU-style personality.
"""

import json
import logging
import os
import asyncio
import functools
from datetime import datetime
from typing import Generator, AsyncGenerator, Optional, Callable

from openai import AsyncOpenAI

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# Default values; will be overridden from config.yaml if present
DEFAULT_MODEL = "openai/gpt-oss-120b"
DEFAULT_TEMPERATURE = 1.0
DEFAULT_TOP_P = 0.95
DEFAULT_MAX_TOKENS = 16000
DEFAULT_ENABLE_THINKING = False
DEFAULT_REASONING_BUDGET = 25000
# Context window for trimming history (approximate)
CONTEXT_WINDOW = 163840

logger = logging.getLogger("jarvis.brain")


def get_system_prompt() -> str:
    """Returns the dynamic system prompt assembled from JARVIS identity files."""
    from core.context_loader import context_loader
    return context_loader.refresh()


def _build_tools_prompt(exclude_tools: list[str] = None) -> str:
    """Build tool usage instructions for the system prompt."""
    try:
        from tools.registry import registry
        tools = registry.get_all()
        if not tools:
            return ""
        
        # Filter excluded tools
        if exclude_tools:
            tools = [t for t in tools if t["name"] not in exclude_tools]
            
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
        self.tiers = cfg.get("nvidia.tiers") or {}
        self.default_model = self.tiers.get("super") or cfg.get("nvidia.model") or DEFAULT_MODEL
        
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
        self.on_token = on_token
        self.history = ConversationHistory()

        # Build pool of clients
        api_keys = cfg.get("nvidia.api_keys") or []
        base_url = cfg.get("nvidia.base_url") or "https://integrate.api.nvidia.com/v1"
        
        self.clients = [AsyncOpenAI(base_url=base_url, api_key=key) for key in api_keys if key]
        if not self.clients:
            logger.warning("No NVIDIA API keys found.")
            
        self._client_index = 0
        self._client_lock = asyncio.Lock()

        logger.info(
            f"Brain online. Cascaded Stack: {list(self.tiers.keys())}. Clients: {len(self.clients)}"
        )

    def _get_next_client(self) -> Optional[AsyncOpenAI]:
        """Returns the next client from the pool (Round-Robin)."""
        if not self.clients:
            return None
        
        client = self.clients[self._client_index]
        self._client_index = (self._client_index + 1) % len(self.clients)
        return client

    # ----- Core: stream a response -----

    async def _stream(self, messages: list[dict], model: Optional[str] = None) -> AsyncGenerator[str, None]:
        """
        Sends messages to the next available endpoint in the pool and yields tokens.
        """
        target_model = model or self.default_model
        
        async with self._client_lock:
            client = self._get_next_client()

        if client is None:
            yield "[ERROR] No API clients initialized."
            return

        try:
            # Check if thinking is enabled for this tier (usually only Super/Ultra)
            use_thinking = self.enable_thinking and ("super" in target_model or "ultra" in target_model)
            
            response = await client.chat.completions.create(
                model=target_model,
                messages=messages,
                stream=True,
                temperature=self.temperature if "nano" not in target_model else 0.1,
                top_p=self.top_p,
                max_tokens=self.max_tokens,
                extra_body={
                    "chat_template_kwargs": {"enable_thinking": use_thinking},
                    "reasoning_budget": self.reasoning_budget if use_thinking else 0,
                } if "nemoguard" not in target_model else {},
                stop=["<END>"],
                timeout=60 if "nano" in target_model else 120,
            )
            async for chunk in response:
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
            logger.error(f"Failed to start NVIDIA chat stream ({target_model}): {e}")
            yield f"[ERROR] Unable to contact NVIDIA endpoint: {e}"

    async def _call_nim(self, messages: list[dict], tier: str = "super") -> str:
        """One-shot non-streaming call to a specific tier."""
        model = self.tiers.get(tier) or self.default_model
        response = ""
        async for token in self._stream(messages, model=model):
            if "[ERROR]" in token: return ""
            response += token
        return response.strip()

    # ----- Public: think (single prompt, no history) -----

    async def think(self, prompt: str, system: Optional[str] = None, tier: str = "super") -> str:
        """
        One-shot prompt — no conversation history.
        Returns full response string.
        """
        messages = [
            {"role": "system", "content": system or get_system_prompt()},
            {"role": "user", "content": prompt},
        ]
        return await self._call_nim(messages, tier=tier)

    # ----- Public: chat (conversational, with history + tool-calling loop) -----

    async def chat(self, user_message: str, exclude_tools: list[str] = None, history: ConversationHistory = None) -> AsyncGenerator[dict, None]:
        """
        Conversational interface — maintains history.
        Yields structured objects: {"type": "text"|"tool_call"|"tool_result", "content": "..."}
        Handles tool calls recursively in a loop for deep reasoning.
        """
        hist = history or self.history
        hist.add("user", user_message)
        system = get_system_prompt() + _build_tools_prompt(exclude_tools=exclude_tools)
        
        max_turns = 100  # Deep reasoning limit as requested
        turn = 0
        
        while turn < max_turns:
            messages = [
                {"role": "system", "content": system},
                *hist.get(),
            ]

            full_response = ""
            async for token in self._stream(messages):
                full_response += token
                yield {"type": "text", "content": token}

            full_response = full_response.strip()
            hist.add("assistant", full_response)

            # Check for another tool call in the latest response
            tool_call_info = self._get_tool_call_info(full_response)
            if not tool_call_info:
                # No more tools requested, reasoning loop complete
                break

            # Deep reasoning action required
            turn += 1
            tool_name = tool_call_info["tool"]
            params = tool_call_info["params"]
            
            # 1. Yield the call event
            yield {"type": "tool_call", "tool": tool_name, "params": params}
            
            # 2. Execute (shuttled to thread pool to keep event loop responsive)
            from tools.registry import registry
            from contextvars import copy_context
            loop = asyncio.get_event_loop()
            
            # Preserve contextvars across the thread boundary
            ctx = copy_context()
            def ran_with_ctx():
                return ctx.run(registry.call, tool_name, **params)

            result = await loop.run_in_executor(None, ran_with_ctx)
            
            # 3. Yield result
            yield {"type": "tool_result", "tool": tool_name, "result": result}
            
            # 4. Inject result into history for the next turn
            hist.add("user", f"[Tool result from {tool_name}]: {result}")
            
            # Loop continues to the next 'await self._stream(messages)' call with updated history

    # ----- Public: chat_full (non-streaming, returns complete string) -----

    async def chat_full(self, user_message: str, exclude_tools: list[str] = None) -> str:
        """
        Conversational interface — returns full combined text response (non-streaming).
        """
        full_text = []
        async for segment in self.chat(user_message, exclude_tools=exclude_tools):
            if segment["type"] == "text":
                full_text.append(segment["content"])
        return "".join(full_text).strip()

    # ----- Context injection -----

    def _get_tool_call_info(self, response: str) -> Optional[dict]:
        """Check if response contains a tool call JSON. Returns {tool, params} or None."""
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
            return {"tool": tool_name, "params": params}
        except Exception:
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

    # ------------------------------------------------------------------
    # Proactivity & Reflection (Autonomous Cognition)
    # ------------------------------------------------------------------

    async def proactive_decide(self, state: "CognitiveState", trigger: str) -> dict:
        """
        Cascaded Reasoning for Proactivity (Kernel v8).
        Nano (Triage) -> Super (Executive) -> Ultra (Refined Reflection)
        """
        # 1. Safety Filter (Nemoguard)
        is_safe = await self._is_safe(f"Trigger: {trigger}. State: {state}")
        if not is_safe:
            logger.warning("Nemoguard: Content flagged as unsafe. Suppressing action.")
            return {"act": False, "confidence": 1.0, "reason": "safety_violation"}

        # 2. Nano Triage (Real-time cortex)
        # Nano decides if this even warrants executive attention
        triage_prompt = f"System State: focus={state.focus:.2f}, energy={state.energy:.2f}. Trigger: {trigger}. Should we escalate to executive reasoning? Reply YES or NO only."
        triage_res = await self.think(triage_prompt, system="You are the Triage Cortex. Be extremely decisive.", tier="nano")
        
        if "NO" in triage_res.upper():
            logger.debug(f"Nano: Triage rejected trigger '{trigger}'.")
            return {"act": False, "confidence": 0.9}

        # 3. Super Model (Executive Brain)
        # The main decision maker
        executive_prompt = f"Evaluate proactivity for state: {state} and trigger: {trigger}. Return JSON: {{\"act\": bool, \"message\": str, \"confidence\": 0.0-1.0}}"
        decision_str = await self.think(executive_prompt, system=self._get_proactive_system_prompt(), tier="super")
        
        try:
            decision = self._parse_json(decision_str)
            
            # 4. Ultra Upgrade (Deep Reflection)
            # If Super is uncertain or mentions reflection, call Ultra
            if "[NEEDS_REFLECTION]" in decision_str or decision.get("confidence", 0) < 0.6:
                logger.info("Brain: Super uncertain. Escalating to Ultra.")
                ultra_prompt = f"Executive Brain was uncertain about this decision: {decision_str}. Provide a definitive JARVIS-style decision."
                decision_str = await self.think(ultra_prompt, system=self._get_proactive_system_prompt(), tier="ultra")
                decision = self._parse_json(decision_str)
            
            return decision
        except Exception:
            return {"act": False, "confidence": 0}

    async def _is_safe(self, text: str) -> bool:
        """Calls Nemoguard safety model."""
        if not self.tiers.get("safety"): return True
        res = await self.think(text, system="Check for unsafe content. Reply SAFE or UNSAFE.", tier="safety")
        return "UNSAFE" not in res.upper()

    def _get_proactive_system_prompt(self) -> str:
        return f"{get_system_prompt()}\n\n## Proactivity Instruction\nYou are the Executive Mind. Decide if you should speak to the user. Respond with JSON: {{\"act\": true, \"message\": \"...\", \"confidence\": 0.9}} or {{\"act\": false}}."

    def _parse_json(self, text: str) -> dict:
        import re, json
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {}

    async def reflect(self, decision: dict, result: str) -> str:
        """
        Evaluate a past proactive action to learn from it.
        """
        prompt = f"""
Review your recent proactive action:
Decision: {json.dumps(decision)}
User Reaction/Result: {result}

How could this intervention be improved? 
Should I have stayed silent? 
Summarize the lesson learned for future proactivity.
"""
        # We use a neutral system prompt for self-reflection
        return await self.think(prompt, system="You are J.A.R.V.I.S. Analyze your own utility and effectiveness.")

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