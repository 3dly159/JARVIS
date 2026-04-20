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
import core.context as ctx

logger = logging.getLogger("jarvis.core")
ROOT = Path(__file__).parent.parent


class JARVISOrchestrator:
    """
    Central orchestrator. All modules live here.
    Initialize once via jarvis.initialize(), then use jarvis.brain, jarvis.memory, etc.
    """

    def __init__(self):
        self.loop = None
        self._initialized = False
        self.conversation_active = False
        self._followup_timer: Optional[threading.Timer] = None

        # Core
        self.brain        = None
        self.memory       = None
        self.context      = None
        self.tasks        = None
        self.agents       = None
        self.cognition    = None
        self.goals        = None

        # Senses
        self.ears         = None
        self.voice        = None
        self.eyes         = None
        self.camera       = None
        self.wake         = None

        # Actions + Tools
        self.actions      = None
        self.tools        = None

        # Skills
        self.skills       = None
        self.skill_manager = None

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

        # Capture the main event loop for background thread communication
        import asyncio
        self.loop = asyncio.get_running_loop()

        self._init_context()
        self._init_memory()
        self._init_tools()
        self._init_brain()
        self._init_monitor()
        self._init_tasks()
        self._init_agents()
        self._init_skills()
        self._init_cognition()

        self._initialized = True
        self.memory.log("JARVIS online.", category="system")
        logger.info("=" * 50)
        logger.info("  J.A.R.V.I.S. — Online")
        logger.info("=" * 50)

    def _init_context(self):
        from core.context_loader import context_loader
        self.context = context_loader
        self.context.refresh()
        
        # Session Reconnaissance: find latest active session from disk
        try:
            sessions_dir = ROOT / "data" / "sessions"
            if sessions_dir.exists():
                session_files = list(sessions_dir.glob("*.json"))
                if session_files:
                    # Sort by modification time (latest first)
                    latest_file = max(session_files, key=lambda f: f.stat().st_mtime)
                    ctx.last_active_session = latest_file.stem
                    logger.info(f"  [1/5] Context synchronized (Focus: {ctx.last_active_session})")
                else:
                    ctx.last_active_session = "default"
                    logger.info("  [1/5] Context synchronized (Focus: default)")
            else:
                ctx.last_active_session = "default"
                logger.info("  [1/5] Context synchronized (Focus: default)")
        except Exception as e:
            logger.warning(f"  [1/5] Context synchronized (Focus error: {e})")
            ctx.last_active_session = "default"

    def _init_memory(self):
        from core.memory import Memory
        self.memory = Memory()
        logger.info("  [2/5] Memory online")

    def _init_tools(self):
        from tools.registry import registry
        # Import tool modules to trigger registration
        from tools import file_browser, web_search, browser_control, memory, agents
        self.tools = registry
        logger.info("  [+] Tools registered")

    def _init_brain(self):
        from core.brain import Brain
        self.brain = Brain()
        # Hot-reload: update brain fields when relevant config changes
        def _on_nvidia_change(key, old, new):
            if not self.brain:
                return
            if key == "nvidia.temperature":
                self.brain.temperature = new
            elif key == "nvidia.top_p":
                self.brain.top_p = new
            elif key == "nvidia.max_tokens":
                self.brain.max_tokens = new
            elif key == "nvidia.enable_thinking":
                self.brain.enable_thinking = new
            elif key == "nvidia.reasoning_budget":
                self.brain.reasoning_budget = new
            elif key == "nvidia.model":
                # model change would require re-instantiating; for simplicity we ignore or could restart.
                pass
        cfg.on_change("nvidia", _on_nvidia_change)
        # Inject memory context into brain
        context_summary = self.memory.get_context_summary()
        self.brain.inject_context(context_summary)
        logger.info("  [3/5] Brain online")

    def _init_monitor(self):
        from system.monitor import monitor
        self.monitor = monitor
        self.monitor.start(interval=cfg.get("monitor.check_interval_seconds", 2))
        logger.info("  [3.5/5] System monitor active")

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
        from core.agent_manager import agent_manager
        self.agents = agent_manager
        self.agents.max_agents = cfg.get("agents.max_agents") or self.agents.max_agents
        self.agents.max_parallel = cfg.get("agents.max_parallel") or self.agents.max_parallel
        self.agents.on_agent_done = self._on_agent_done
        self.agents.start()
        logger.info("  [5/5] Agent manager online")

    def _init_skills(self):
        from skills.loader import skill_loader
        from skills.manager import skill_manager
        self.skills = skill_loader
        self.skill_manager = skill_manager
        skill_loader.load_all()
        # Inject skill context into brain
        skill_context = skill_loader.get_context()
        if skill_context and skill_context != "No skills loaded.":
            self.brain.inject_context(f"Skills available:\n{skill_context}")

        # Register skill tools with registry
        from tools.registry import registry
        registry.register(
            name="install_skill",
            description="Install a new skill from ClawHub by name.",
            handler=lambda skill_name, **_: skill_manager.install(skill_name)["message"],
            params={"skill_name": "name of the skill to install from clawhub"},
        )
        registry.register(
            name="search_skills",
            description="Search ClawHub for available skills.",
            handler=lambda query, **_: skill_manager.search(query),
            params={"query": "what kind of skill to search for"},
        )
        registry.register(
            name="list_skills",
            description="List all currently installed JARVIS skills.",
            handler=lambda **_: skill_loader.get_summary(),
            params={},
        )
        logger.info(f"  [+] Skills loaded: {skill_loader.status()['loaded']} skill(s)")

    def _init_cognition(self):
        from core.cognition import cognition
        from core.goal_manager import goal_manager
        self.cognition = cognition
        self.goals = goal_manager
        self.cognition.start()
        logger.info("  [6/5] Cognition loop active (Nervous system online)")

    # ------------------------------------------------------------------
    # Late-init senses (called after core is up)
    # ------------------------------------------------------------------

    def init_senses(self):
        """Initialize senses via modular singletons."""
        try:
            from senses.voice import voice
            self.voice = voice
            self.voice.on_finished = self._handle_speech_finished
            # Hot-reload voice settings
            cfg.on_change("voice", lambda k, o, n: self.voice.update(cfg.section("voice")) if self.voice else None)
            logger.info("  [senses] Voice online")
        except Exception as e:
            logger.warning(f"  [senses] Voice unavailable: {e}")

        try:
            from senses.ears import ears
            self.ears = ears
            logger.info("  [senses] Ears online")
        except Exception as e:
            logger.warning(f"  [senses] Ears unavailable: {e}")

        try:
            from senses.eyes import eyes
            self.eyes = eyes
            logger.info("  [senses] Eyes online")
        except Exception as e:
            logger.warning(f"  [senses] Eyes unavailable: {e}")

        try:
            from senses.wake import wake_listener
            self.wake = wake_listener
            self.wake.start(on_wake=self._on_wake)
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
                quiet_hours_enabled=cfg.get("notifications.quiet_hours_enabled"),
            )
            cfg.on_change("notifications", lambda k, o, n: self.notifier.update(cfg.section("notifications")) if self.notifier else None)
            cfg.on_change("notifications", lambda k, o, n: self.voice.update(cfg.section("notifications")) if self.voice else None)
            logger.info("  [notif] Notifier online")
        except Exception as e:
            logger.warning(f"  [notif] Notifier unavailable: {e}")

    def init_ui(self):
        """Initialize the web UI server."""
        try:
            from api.server import UIServer
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

    def _require_initialized(self):
        if not self._initialized:
            raise RuntimeError("JARVIS not initialized. Call initialize() first.")

    def _broadcast_state(self, state: str):
        if self.ui:
            self.ui.broadcast("state", {"status": state})

    def interrupt(self):
        """Stop current activity and reset state."""
        if self.voice:
            self.voice.stop()
        self._broadcast_state("interrupted")
        self.memory.log("Interruption requested.", category="system")
        
        # If we were in a follow-up, reset it
        if self._followup_timer:
            self._followup_timer.cancel()
            self._followup_timer = None
        
        self.conversation_active = False

    async def chat(self, user_input: str) -> str:
        """
        Main entry point for user input.
        If called via voice (no session context), falls back to last active session
        and broadcasts to UI.
        """
        self._require_initialized()
        
        # Resolve target session
        session_id = ctx.session_id_ctx.get() or ctx.last_active_session or "default"
        is_voice = ctx.session_id_ctx.get() is None
        
        # Handle silence / empty input (usually from voice follow-up timeout)
        if not user_input or not user_input.strip():
            if is_voice and self.conversation_active:
                logger.info("Silence detected. Returning to idle...")
                self.conversation_active = False
                self._broadcast_state("idle")
            return ""

        # If voice, notify UI we are receiving speech
        if is_voice and session_id:
            try:
                from api.routes.chat import chat_broadcaster, save_session_message
                save_session_message(session_id, "user", f"[Voice]: {user_input}")
                await chat_broadcaster.send(session_id, {
                    "segment": {"type": "text", "content": f"\n\n[Voice]: {user_input}\n", "role": "user"},
                    "done": False,
                    "source": "voice"
                })
            except Exception: pass

        self.memory.log_conversation("user", user_input)
        self._broadcast_state("thinking")
        
        # Notify cognition of activity
        if self.cognition:
            self.cognition.state_builder.update_interaction()

        task_summary = self.tasks.summary()
        if task_summary != "No active tasks.":
            self.brain.inject_context(f"Current tasks:\n{task_summary}")

        response = await self.brain.chat_full(user_input)
        self.memory.log_conversation("jarvis", response)

        # Broadcast response to UI if voice-triggered
        if is_voice and session_id:
            try:
                from api.routes.chat import chat_broadcaster, save_session_message
                save_session_message(session_id, "jarvis", response)
                await chat_broadcaster.send(session_id, {
                    "segment": {"type": "text", "content": response, "role": "assistant"},
                    "done": True,
                    "source": "voice"
                })
            except Exception: pass

        if self.voice:
            # SANITIZE: Ensure we don't speak raw JSON or data blocks
            clean_response = self._sanitize_for_speech(response)
            if clean_response:
                logger.info(f"Handing off to voice engine: {clean_response[:60]}...")
                self.voice.speak(clean_response)
            
            # If this is a vocal interaction, activate Follow-up Mode
            if is_voice:
                self._start_followup_loop(session_id)
        
        # We don't broadcast idle here anymore; voice on_finished or follow-up loop handles it
        return response

    def _start_followup_loop(self, session_id: str):
        """Prepares for a follow-up interaction."""
        self.conversation_active = True
        logger.info("Conversation active. Waiting for speech to finish...")

    def _handle_speech_finished(self):
        """Triggered by Voice engine when playback ends."""
        if not self.conversation_active:
            return
            
        logger.info("Follow-up window open. Listening...")
        self._broadcast_state("listening")
        
        try:
            from senses.ears import ears
            # Listen once for a reply. If captured, chat() will be called, 
            # which will then re-trigger _start_followup_loop.
            ears.listen_once(callback=self.chat)
        except Exception as e:
            logger.error(f"Follow-up error: {e}")
            self.conversation_active = False

    async def chat_stream(self, user_input: str):
        """
        Streaming version of chat. Yields structured dictionaries.
        Logs conversation when complete. Broadcasts state changes.
        """
        self._require_initialized()
        self.memory.log_conversation("user", user_input)
        self._broadcast_state("thinking")

        full_text = ""
        voice_text = ""
        
        # We accumulate text to speak, but only if it doesn't look like a tool call block
        async for segment in self.brain.chat(user_input):
            yield segment
            
            if segment["type"] == "text":
                token = segment["content"]
                full_text += token
                
                # Simple logic: if the current accumulated text in this segment block 
                # doesn't start with a tool-call JSON brace, we consider it "speakable".
                voice_text += token

        # Persist the full raw log (including tool calls if they were in the text)
        self.memory.log_conversation("jarvis", full_text)

        # Trigger voice only for "clean" text
        if self.voice:
            clean_voice = self._sanitize_for_speech(voice_text)
            if clean_voice:
                self.voice.speak(clean_voice)

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

    async def _on_agent_done(self, agent, result):
        logger.info(f"Agent done: {agent.name}")
        self.memory.log(f"Agent '{agent.name}' finished. Result: {result[:100]}", category="agent")
        
        # Audio notification
        if self.voice:
            self.voice.speak(f"Sir, the {agent.name} mission is complete.")

        # UI Notification
        if self.notifier:
            self.notifier.info(f"Agent '{agent.name}' task complete, sir.")

        # Session Reporting: If spawned from chat, send result to the UI
        if agent.session_id:
            try:
                from api.routes.chat import chat_broadcaster, save_session_message
                
                report_title = f"MISSION REPORT: {agent.name}"
                formatted_result = f"### {report_title}\n\n{result}"
                
                # Broadcaster push (live UI update)
                payload = {
                    "segment": {"type": "text", "content": f"\n\n---\n{formatted_result}\n---"},
                    "done": True,
                    "agent_id": agent.id
                }
                await chat_broadcaster.send(agent.session_id, payload)
                
                # History Persistence
                save_session_message(
                    session_id=agent.session_id, 
                    role="jarvis", 
                    content=formatted_result,
                    parts=[{"type": "text", "text": formatted_result}]
                )
                logger.debug(f"Mission report delivered to session {agent.session_id}")
            except Exception as e:
                logger.error(f"Failed to deliver mission report: {e}")

    def _on_wake(self, source: str):
        """Standard wake word trigger."""
        if not self._initialized: return
        logger.info(f"Wake triggered via {source}")

        # Broadcast state locally
        self._broadcast_state("speaking")

        if self.voice:
            self.voice.speak_now("Yes sir?")
        
        # After saying "Yes sir?", start listening (which will broadcast "listening")
        if self.ears:
            self.ears.listen_once(callback=self.chat)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _broadcast_state(self, state: str):
        """Broadcast state to all connected UI clients."""
        logger.debug(f"State transition: {state}")
        try:
            from api.routes.state import set_state_sync
            set_state_sync(state)
        except Exception as e:
            logger.error(f"Failed to broadcast state '{state}': {e}")

    def _require_initialized(self):
        if not self._initialized:
            raise RuntimeError("JARVIS not initialized. Call jarvis.initialize() first.")

    def say(self, text: str):
        """Speak text directly (bypasses brain)."""
        if self.voice:
            self.voice.speak(text)
        else:
            logger.info(f"[JARVIS would say]: {text}")

    def ask(self, question: str, timeout: float = 10.0) -> str:
        """
        Speak a question and listen for a spoken response.
        Returns transcribed text or empty string.
        """
        if self.voice:
            self.voice.speak_now(question)
        if self.ears:
            return self.ears.listen_once(timeout=timeout)
        return ""

    def confirm_voice(self, description: str, action_type: str = "general") -> bool:
        """
        Ask for voice confirmation. Convenience wrapper.
        Returns True if approved.
        """
        from actions.confirm import confirm as gate
        return gate.request(description, action_type=action_type, voice_prompt=True)

    def _sanitize_for_speech(self, text: str) -> str:
        """
        Strips technical artifacts (JSON, Markdown, Tool calls) from text 
        to ensure only natural language is spoken.
        """
        if not text:
            return ""
            
        import re
        
        # 1. Remove Markdown code blocks (```...``` or `...`)
        # Use DOTALL to catch multi-line blocks
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`.*?`', '', text)
        
        # 2. Remove JSON-like blocks (anything between balanced braces that looks technical)
        # For simplicity, we remove all { ... } blocks that contain typical JSON keys
        text = re.sub(r'\{.*?"(tool|action|args|result|status)".*?\}', '', text, flags=re.DOTALL)
        
        # 3. Remove raw tool call indicators (e.g. Call: tool_name)
        text = re.sub(r'(Call|Tool|Action|Result):\s*.*', '', text, flags=re.IGNORECASE)
        
        # 4. Clean up any leftover Markdown artifacts
        text = re.sub(r'([\#\*\-\+\>\_\~\[\]\(\)])', '', text)
        
        # 5. Collapse multiple white spaces/newlines
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def status(self) -> dict:
        return {
            "initialized": self._initialized,
            "brain": self.brain.status() if self.brain else None,
            "memory": self.memory.status() if self.memory else None,
            "tasks": self.tasks.status() if self.tasks else None,
            "agents": self.agents.status() if self.agents else None,
            "skills": self.skills.status() if self.skills else None,
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
