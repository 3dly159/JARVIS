"""
actions/confirm.py - JARVIS Confirmation Gate

Approval gate for dangerous or irreversible actions.
JARVIS asks the user before executing anything risky.

Usage:
    from actions.confirm import confirm
    if confirm.request("delete file /home/user/doc.txt"):
        do_the_thing()
"""

import logging
import threading
import time
from typing import Callable, Optional

logger = logging.getLogger("jarvis.confirm")


class ConfirmationGate:
    """
    Manages approval requests for dangerous actions.
    Supports voice prompt, UI popup, and CLI fallback.
    """

    def __init__(
        self,
        timeout_seconds: int = 30,
        require_for: list = None,
    ):
        self.timeout_seconds = timeout_seconds
        self.require_for = require_for or ["shell_command", "file_delete", "keyboard_mouse"]
        self._pending: dict[str, dict] = {}  # request_id → {event, approved}
        self._lock = threading.Lock()

    def requires_confirmation(self, action_type: str) -> bool:
        """Check if this action type needs confirmation."""
        return action_type in self.require_for

    def request(
        self,
        description: str,
        action_type: str = "general",
        timeout: Optional[int] = None,
        voice_prompt: bool = True,
    ) -> bool:
        """
        Request confirmation for an action.
        Blocks until approved, denied, or timeout.
        Returns True if approved, False otherwise.
        """
        if not self.requires_confirmation(action_type):
            return True

        timeout = timeout or self.timeout_seconds
        request_id = f"{action_type}_{int(time.time())}"

        event = threading.Event()
        with self._lock:
            self._pending[request_id] = {
                "description": description,
                "action_type": action_type,
                "event": event,
                "approved": False,
                "timestamp": time.time(),
            }

        # Announce via voice and listen for spoken response
        if voice_prompt:
            self._voice_prompt_and_listen(request_id, description, timeout)

        logger.info(f"Awaiting confirmation [{request_id}]: {description}")
        print(f"\n⚠️  JARVIS needs confirmation:\n   {description}\n   Approve? [y/N] (timeout: {timeout}s): ", end="", flush=True)

        # Wait for approval (from voice, UI, or CLI)
        approved = event.wait(timeout=timeout)

        with self._lock:
            if request_id in self._pending:
                result = self._pending[request_id]["approved"] if approved else False
                del self._pending[request_id]
            else:
                result = False

        if not approved:
            logger.warning(f"Confirmation timed out: {description}")
            print("(timed out — denied)")
        else:
            logger.info(f"Confirmation {'approved' if result else 'denied'}: {description}")

        return result

    def approve(self, request_id: str):
        """Approve a pending request (called from UI or voice handler)."""
        with self._lock:
            if request_id in self._pending:
                self._pending[request_id]["approved"] = True
                self._pending[request_id]["event"].set()

    def deny(self, request_id: str):
        """Deny a pending request."""
        with self._lock:
            if request_id in self._pending:
                self._pending[request_id]["approved"] = False
                self._pending[request_id]["event"].set()

    # ------------------------------------------------------------------
    # Voice prompt + listen
    # ------------------------------------------------------------------

    def _voice_prompt_and_listen(self, request_id: str, description: str, timeout: int):
        """
        Speak the confirmation prompt, then listen for a yes/no response.
        Runs in a background thread so it doesn't block the main wait.
        """
        def _speak_and_listen():
            try:
                from core.jarvis import jarvis

                # Speak the request
                if jarvis.voice:
                    jarvis.voice.speak_now(
                        f"Confirmation required, sir. {description}. "
                        f"Say yes to confirm or no to cancel."
                    )

                # Listen for response (shorter timeout than full action timeout)
                if jarvis.ears:
                    listen_timeout = min(timeout - 2, 10)
                    text = jarvis.ears.listen_once(timeout=float(listen_timeout))
                    if text:
                        self._handle_voice_response(request_id, text)
            except Exception as e:
                logger.debug(f"Voice confirmation error: {e}")

        threading.Thread(target=_speak_and_listen, daemon=True).start()

    def _handle_voice_response(self, request_id: str, text: str):
        """
        Parse spoken yes/no and approve/deny the request.
        """
        text_lower = text.lower().strip()
        YES_WORDS = ("yes", "yeah", "yep", "confirm", "proceed", "do it",
                     "go ahead", "approved", "sure", "okay", "ok")
        NO_WORDS  = ("no", "nope", "cancel", "stop", "deny", "don't",
                     "abort", "negative", "never")

        if any(w in text_lower for w in YES_WORDS):
            logger.info(f"Voice confirmation: APPROVED ('{text}')")
            try:
                from core.jarvis import jarvis
                if jarvis.voice:
                    jarvis.voice.speak("Confirmed. Proceeding, sir.")
            except Exception:
                pass
            self.approve(request_id)

        elif any(w in text_lower for w in NO_WORDS):
            logger.info(f"Voice confirmation: DENIED ('{text}')")
            try:
                from core.jarvis import jarvis
                if jarvis.voice:
                    jarvis.voice.speak("Understood. Action cancelled.")
            except Exception:
                pass
            self.deny(request_id)

        else:
            # Unclear response — ask once more
            logger.debug(f"Voice confirmation unclear: '{text}' — asking again")
            try:
                from core.jarvis import jarvis
                if jarvis.voice:
                    jarvis.voice.speak_now("I didn't catch that. Yes to confirm, no to cancel.")
                if jarvis.ears:
                    retry = jarvis.ears.listen_once(timeout=8.0)
                    if retry:
                        self._handle_voice_response(request_id, retry)
            except Exception as e:
                logger.debug(f"Voice retry error: {e}")

    def cli_respond(self, response: str) -> bool:
        """Handle CLI y/n response for the most recent pending request."""
        with self._lock:
            if not self._pending:
                return False
            # Get most recent
            request_id = max(self._pending, key=lambda k: self._pending[k]["timestamp"])
            approved = response.strip().lower() in ("y", "yes")
            self._pending[request_id]["approved"] = approved
            self._pending[request_id]["event"].set()
            return approved

    def list_pending(self) -> list[dict]:
        with self._lock:
            return [
                {"id": rid, "description": v["description"], "action_type": v["action_type"]}
                for rid, v in self._pending.items()
            ]

    def status(self) -> dict:
        return {
            "pending_count": len(self._pending),
            "timeout_seconds": self.timeout_seconds,
            "require_for": self.require_for,
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

from core.config_manager import config

confirm = ConfirmationGate(
    timeout_seconds=config.get("actions.confirmation_timeout_seconds", 30),
    require_for=config.get("actions.require_confirmation", ["shell_command", "file_delete", "keyboard_mouse"]),
)
