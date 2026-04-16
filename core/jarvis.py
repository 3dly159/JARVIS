"""
core/jarvis.py - JARVIS Orchestrator

The central hub. Holds references to every module.
All modules import `jarvis` from here instead of importing each other.
This prevents circular imports and gives a single source of truth.

Usage:
    from core.jarvis import jarvis
    jarvis.brain.chat("Hello")
    jarvis.memory.log("Something happened")
    jarvis.tasks.create("Do something")
"""

import logging
from pathlib import Path
from typing import Optional
from core.config_manager import config as cfg

logger = logging.getLogger("jarvis.core")
ROOT = Path(__file__).parent.parent


class JARVISOrchestrator:
    """
    Central orchestrator. All modules live here.
    Initialize once via jarvis.initialize(), then use jarvis.brain, jarvis.memory, etc.
    """

    def __init__(self):
        self.config: dict = {}
        self._initialized = False

        # Core
        self.brain        = None
        self.memory       = None
        self.context      = None
        self.tasks        = None
        self.agents       = None

        # Senses
        self.ears         = None
        self.voice        = None
        self.eyes         = None
        self.camera       = None
        self.wake         = None

        # Actions + Tools
        self.actions      = None
        self.tools        = None

        # Notifications
        self.notifier     = None

        # UI
        self.ui           = None

        # System
        self.monitor      = None

    # ------------------------------------------------------------------
    # Initialize
    # ------------------------------------------------------------------

    def initialize(self, config: Optional[dict] = None):
        if self._initialized:
            logger.warning("Already initialized.")
            return

        self.config = cfg.all()
        logger.info("=" * 50)
        logger.info("  J.A.R.V.I.S. — Initializing")
        logger.info("=" * 50)

        self._init_context()
        self._init_memory()
        self._init_brain()
        self._init_tasks()
        self._init_agents()

        self._initialized = True
        self.memory.log("JARVIS online.", category="system")
        logger.info("=" * 50)
        logger.info("  J.A.R.V.I.S. — Online")
        logger.info("=" * 50)

    def _init_context(self):
        from core.context_loader import ContextLoader
        self.context = ContextLoader(root=ROOT)
        self.context.refresh()
        logger.info("  [1/5] Context loaded")

    def _init_memory(self):
        from core.memory import Memory
        self.memory = Memory()
        logger.info("  [2/5] Memory online")

    def _init_brain(self):
        from core.brain import Brain
        self.brain = Brain(
            model=cfg.get("llm.model"),
            ollama_host=cfg.get("llm.ollama_host"),
            temperature=cfg.get("llm.temperature"),
        )
        # Hot-reload: update temperature when config changes
        cfg.on_change("llm", lambda key, old, new: setattr(self.brain, "temperature", cfg.get("llm.temperature")) if self.brain else None)
        # Inject memory context into brain
        context_summary = self.memory.get_context_summary()
        self.brain.inject_context(context_summary)
        logger.info("  [3/5] Brain online")

    def _init_tasks(self):
        from core.task_tracker import TaskTracker
        self.tasks = TaskTracker(
            self_ping_interval=cfg.get("tasks.self_ping_interval_seconds"),
            stall_threshold=cfg.get("tasks.stall_threshold_minutes"),
            on_stall=self._on_task_stall,
            on_overdue=self._on_task_overdue,
            on_complete=self._on_task_complete,
        )
        self.tasks.start()
        logger.info("  [4/5] Task tracker online")

    def _init_agents(self):
        from core.agent_manager import AgentManager
        self.agents = AgentManager(
            max_agents=cfg.get("agents.max_agents"),
            max_parallel=cfg.get("agents.max_parallel"),
            on_agent_done=self._on_agent_done,
        )
        self.agents.start()
        logger.info("  [5/5] Agent manager online")

    # ------------------------------------------------------------------
    # Late-init senses (called after core is up)
    # ------------------------------------------------------------------

    def init_senses(self):
        """Initialize senses. Called after core is confirmed working."""
        try:
            from senses.voice import Voice
            self.voice = Voice(
                voice=cfg.get("voice.tts_voice"),
                rate=cfg.get("voice.tts_rate"),
                pitch=cfg.get("voice.tts_pitch"),
            )
            # Hot-reload voice settings
            cfg.on_change("voice", lambda k, o, n: self.voice.update(cfg.section("voice")) if self.voice else None)
            logger.info("  [senses] Voice online")
        except Exception as e:
            logger.warning(f"  [senses] Voice unavailable: {e}")

        try:
            from senses.ears import Ears
            self.ears = Ears(
                model_size=cfg.get("voice.stt_model"),
                device=cfg.get("voice.stt_device"),
            )
            logger.info("  [senses] Ears online")
        except Exception as e:
            logger.warning(f"  [senses] Ears unavailable: {e}")

        try:
            from senses.eyes import Eyes
            self.eyes = Eyes()
            logger.info("  [senses] Eyes online")
        except Exception as e:
            logger.warning(f"  [senses] Eyes unavailable: {e}")

        try:
            from senses.wake import WakeListener
            self.wake = WakeListener(
                wake_word=cfg.get("voice.wake_word"),
                hotkey=cfg.get("voice.hotkey"),
                on_wake=self._on_wake,
            )
            logger.info("  [senses] Wake listener online")
        except Exception as e:
            logger.warning(f"  [senses] Wake listener unavailable: {e}")

    def init_notifications(self):
        """Initialize notification system."""
        try:
            from notifications.notifier import Notifier
            self.notifier = Notifier(
                voice_alerts=cfg.get("notifications.voice_alerts"),
                tray_enabled=cfg.get("notifications.tray_enabled"),
                quiet_start=cfg.get("notifications.quiet_hours_start"),
                quiet_end=cfg.get("notifications.quiet_hours_end"),
            )
            cfg.on_change("notifications", lambda k, o, n: self.notifier.update(cfg.section("notifications")) if self.notifier else None)
            logger.info("  [notif] Notifier online")
        except Exception as e:
            logger.warning(f"  [notif] Notifier unavailable: {e}")

    def init_ui(self):
        """Initialize the web UI server."""
        try:
            from ui.server import UIServer
            self.ui = UIServer(
                host=cfg.get("ui.host"),
                port=cfg.get("ui.port"),
            )
            logger.info(f"  [ui] UI server ready at http://{cfg.get('ui.host')}:{cfg.get('ui.port')}")
        except Exception as e:
            logger.warning(f"  [ui] UI unavailable: {e}")

    # ------------------------------------------------------------------
    # Main conversation interface
    # ------------------------------------------------------------------

    def chat(self, user_input: str) -> str:
        """
        Main entry point for user input.
        Logs conversation, sends to brain, logs response.
        Returns full response string.
        """
        self._require_initialized()

        # Log user input
        self.memory.log_conversation("user", user_input)

        # Inject fresh task summary before responding
        task_summary = self.tasks.summary()
        if task_summary != "No active tasks.":
            self.brain.inject_context(f"Current tasks:\n{task_summary}")

        # Get response
        response = self.brain.chat_full(user_input)

        # Log JARVIS response
        self.memory.log_conversation("jarvis", response)

        # Speak if voice is available
        if self.voice:
            self.voice.speak(response)

        return response

    def chat_stream(self, user_input: str):
        """
        Streaming version of chat. Yields tokens as they arrive.
        Logs conversation when complete.
        """
        self._require_initialized()
        self.memory.log_conversation("user", user_input)

        full_response = ""
        for token in self.brain.chat(user_input):
            full_response += token
            yield token

        self.memory.log_conversation("jarvis", full_response)

        if self.voice and full_response:
            self.voice.speak(full_response)

    # ------------------------------------------------------------------
    # Event handlers (called by modules)
    # ------------------------------------------------------------------

    def _on_task_stall(self, task):
        msg = f"Task '{task.title}' has stalled, sir. Shall I investigate?"
        logger.warning(f"Task stalled: {task.id}")
        self.memory.log(f"Task stalled: {task.title}", category="warning")
        if self.notifier:
            self.notifier.alert(msg, priority="warning")

    def _on_task_overdue(self, task):
        msg = f"Task '{task.title}' is overdue."
        logger.warning(f"Task overdue: {task.id}")
        self.memory.log(f"Task overdue: {task.title}", category="warning")
        if self.notifier:
            self.notifier.alert(msg, priority="warning")

    def _on_task_complete(self, task):
        msg = f"Task complete: '{task.title}'."
        logger.info(f"Task done: {task.id}")
        self.memory.log(f"Task complete: {task.title}", category="system")
        if self.notifier:
            self.notifier.alert(msg, priority="info")

    def _on_agent_done(self, agent, result):
        logger.info(f"Agent done: {agent.name}")
        self.memory.log(f"Agent '{agent.name}' finished. Result: {result[:100]}", category="agent")

    def _on_wake(self, source: str):
        """Called when wake word or hotkey is triggered."""
        logger.info(f"Wake triggered via {source}")
        if self.voice:
            self.voice.speak("Yes, sir?")
        if self.ears:
            self.ears.listen_once(callback=self.chat)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _require_initialized(self):
        if not self._initialized:
            raise RuntimeError("JARVIS not initialized. Call jarvis.initialize() first.")

    def say(self, text: str):
        """Speak text directly (bypasses brain)."""
        if self.voice:
            self.voice.speak(text)
        else:
            logger.info(f"[JARVIS would say]: {text}")

    def status(self) -> dict:
        return {
            "initialized": self._initialized,
            "brain": self.brain.status() if self.brain else None,
            "memory": self.memory.status() if self.memory else None,
            "tasks": self.tasks.status() if self.tasks else None,
            "agents": self.agents.status() if self.agents else None,
            "voice": self.voice is not None,
            "ears": self.ears is not None,
            "eyes": self.eyes is not None,
            "wake": self.wake is not None,
            "notifier": self.notifier is not None,
            "ui": self.ui is not None,
        }


# ---------------------------------------------------------------------------
# Singleton — import this everywhere
# ---------------------------------------------------------------------------

jarvis = JARVISOrchestrator()
