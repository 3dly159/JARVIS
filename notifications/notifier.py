"""
notifications/notifier.py - JARVIS Notifier

Central dispatch for all alerts and notifications.
Routes to: voice, system tray, sound.
Respects quiet hours and priority levels.

Usage:
    from notifications.notifier import notifier
    notifier.alert("Task stalled, sir.", priority="warning")
    notifier.info("Download complete.")
    notifier.urgent("System CPU at 95%!")
"""

import logging
import threading
from datetime import datetime
from typing import Optional

logger = logging.getLogger("jarvis.notifier")

PRIORITIES = ("info", "warning", "urgent")


class Notifier:
    """
    Central notification dispatcher.
    Sends alerts via voice, tray, and sound based on priority.
    """

    def __init__(
        self,
        voice_alerts: bool = True,
        tray_enabled: bool = True,
        sound_enabled: bool = True,
        quiet_start: str = "23:00",
        quiet_end: str = "08:00",
        quiet_hours_enabled: bool = False,
    ):
        self.voice_alerts = voice_alerts
        self.tray_enabled = tray_enabled
        self.sound_enabled = sound_enabled
        self.quiet_start = quiet_start
        self.quiet_end = quiet_end
        self.quiet_hours_enabled = quiet_hours_enabled
        self._history: list[dict] = []
        logger.info("Notifier online.")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def alert(self, message: str, priority: str = "info", title: str = "JARVIS"):
        """
        Send a notification.
        priority: "info" | "warning" | "urgent"
        """
        if priority not in PRIORITIES:
            priority = "info"

        entry = {
            "time": datetime.now().isoformat(),
            "priority": priority,
            "title": title,
            "message": message,
        }
        self._history.append(entry)
        logger.info(f"[{priority.upper()}] {message}")

        # Dispatch in background thread
        threading.Thread(
            target=self._dispatch,
            args=(message, priority, title),
            daemon=True,
        ).start()

    def info(self, message: str, title: str = "JARVIS"):
        self.alert(message, priority="info", title=title)

    def warning(self, message: str, title: str = "JARVIS"):
        self.alert(message, priority="warning", title=title)

    def urgent(self, message: str, title: str = "JARVIS"):
        self.alert(message, priority="urgent", title=title)

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def _dispatch(self, message: str, priority: str, title: str):
        """Route notification to appropriate channels."""
        quiet = self.quiet_hours_enabled and self._is_quiet_hours()

        # Voice: always for urgent, respect quiet hours for others
        if self.voice_alerts and (priority == "urgent" or not quiet):
            self._speak(message)

        # Tray: always show (quiet hours don't suppress tray)
        if self.tray_enabled:
            self._tray(title, message, priority)

        # Sound: urgent always, others respect quiet hours
        if self.sound_enabled and (priority == "urgent" or not quiet):
            self._sound(priority)

    def _speak(self, message: str):
        try:
            from core.jarvis import jarvis
            if jarvis.voice:
                jarvis.voice.speak(message)
        except Exception as e:
            logger.debug(f"Voice alert failed: {e}")

    def _tray(self, title: str, message: str, priority: str):
        try:
            from plyer import notification
            icons = {"info": "", "warning": "⚠️", "urgent": "🚨"}
            notification.notify(
                title=f"{icons.get(priority, '')} {title}",
                message=message,
                timeout=8 if priority == "urgent" else 5,
            )
        except ImportError:
            logger.debug("plyer not installed — tray notifications unavailable.")
        except Exception as e:
            logger.debug(f"Tray notification failed: {e}")

    def _sound(self, priority: str):
        try:
            from notifications.sounds import sounds
            sounds.play(priority)
        except Exception as e:
            logger.debug(f"Sound alert failed: {e}")

    # ------------------------------------------------------------------
    # Quiet hours
    # ------------------------------------------------------------------

    def _is_quiet_hours(self) -> bool:
        try:
            now = datetime.now().strftime("%H:%M")
            start, end = self.quiet_start, self.quiet_end
            if start <= end:
                return start <= now <= end
            return now >= start or now <= end
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Hot-reload
    # ------------------------------------------------------------------

    def update(self, settings: dict):
        if "voice_alerts" in settings:
            self.voice_alerts = settings["voice_alerts"]
        if "tray_enabled" in settings:
            self.tray_enabled = settings["tray_enabled"]
        if "quiet_hours_start" in settings:
            self.quiet_start = settings["quiet_hours_start"]
        if "quiet_hours_end" in settings:
            self.quiet_end = settings["quiet_hours_end"]
        if "quiet_hours_enabled" in settings:
            self.quiet_hours_enabled = settings["quiet_hours_enabled"]
        logger.info("Notifier settings updated.")

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def get_history(self, limit: int = 20) -> list[dict]:
        return self._history[-limit:]

    def clear_history(self):
        self._history.clear()

    def status(self) -> dict:
        return {
            "voice_alerts": self.voice_alerts,
            "tray_enabled": self.tray_enabled,
            "sound_enabled": self.sound_enabled,
            "quiet_hours_enabled": self.quiet_hours_enabled,
            "quiet_hours": f"{self.quiet_start} - {self.quiet_end}",
            "in_quiet_hours": self.quiet_hours_enabled and self._is_quiet_hours(),
            "history_count": len(self._history),
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

from core.config_manager import config

notifier = Notifier(
    voice_alerts=config.get("notifications.voice_alerts", True),
    tray_enabled=config.get("notifications.tray_enabled", True),
    quiet_start=config.get("notifications.quiet_hours_start", "23:00"),
    quiet_end=config.get("notifications.quiet_hours_end", "08:00"),
    quiet_hours_enabled=config.get("notifications.quiet_hours_enabled", True),
)
