"""
actions/app_control.py - JARVIS App Control

Open, close, focus, and manage application windows.
Cross-platform (Linux primary, Windows compatible).

Usage:
    from actions.app_control import apps
    apps.open("firefox")
    apps.focus("Terminal")
    apps.close("firefox")
    apps.list_windows()
"""

import logging
import os
import platform
import subprocess
import time
from typing import Optional

logger = logging.getLogger("jarvis.apps")

PLATFORM = platform.system().lower()  # "linux", "windows", "darwin"


class AppControl:
    """Open, close, and manage application windows."""

    # ------------------------------------------------------------------
    # Open
    # ------------------------------------------------------------------

    def open(self, app: str, args: str = "", confirm: bool = False) -> bool:
        """
        Open an application.
        app: application name or path (e.g. "firefox", "gedit", "code")
        """
        if confirm:
            from actions.confirm import confirm as gate
            if not gate.request(f"Open application: {app}", action_type="app_open"):
                return False

        cmd = self._build_open_cmd(app, args)
        try:
            subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._log(f"Opened: {app}")
            logger.info(f"Opened application: {app}")
            return True
        except Exception as e:
            logger.error(f"Failed to open {app}: {e}")
            return False

    def _build_open_cmd(self, app: str, args: str = "") -> str:
        suffix = f" {args}" if args else ""
        if PLATFORM == "linux":
            return f"{app}{suffix} &"
        elif PLATFORM == "windows":
            return f"start {app}{suffix}"
        elif PLATFORM == "darwin":
            return f"open -a {app}{suffix}"
        return f"{app}{suffix}"

    # ------------------------------------------------------------------
    # Close
    # ------------------------------------------------------------------

    def close(self, app: str, confirm: bool = True, force: bool = False) -> bool:
        """Close an application by name."""
        if confirm:
            from actions.confirm import confirm as gate
            if not gate.request(f"Close application: {app}", action_type="app_close"):
                return False

        try:
            if PLATFORM == "linux":
                cmd = f"pkill -{'9 -' if force else ''}f '{app}'"
            elif PLATFORM == "windows":
                cmd = f"taskkill /{'F ' if force else ''}/IM {app}.exe"
            else:
                cmd = f"pkill {app}"

            result = subprocess.run(cmd, shell=True, capture_output=True)
            success = result.returncode == 0
            if success:
                self._log(f"Closed: {app}")
                logger.info(f"Closed application: {app}")
            else:
                logger.warning(f"Could not close {app} (not running?)")
            return success
        except Exception as e:
            logger.error(f"Close app error: {e}")
            return False

    # ------------------------------------------------------------------
    # Focus
    # ------------------------------------------------------------------

    def focus(self, window_title: str) -> bool:
        """Bring a window to focus by title (partial match)."""
        try:
            if PLATFORM == "linux":
                # Use wmctrl if available
                result = subprocess.run(
                    f"wmctrl -a '{window_title}'",
                    shell=True, capture_output=True
                )
                if result.returncode == 0:
                    logger.info(f"Focused: {window_title}")
                    return True

                # Fallback: xdotool
                result = subprocess.run(
                    f"xdotool search --name '{window_title}' windowactivate",
                    shell=True, capture_output=True
                )
                return result.returncode == 0

            elif PLATFORM == "windows":
                try:
                    import pygetwindow as gw
                    wins = gw.getWindowsWithTitle(window_title)
                    if wins:
                        wins[0].activate()
                        return True
                except ImportError:
                    pass
            return False

        except Exception as e:
            logger.error(f"Focus error: {e}")
            return False

    # ------------------------------------------------------------------
    # List windows
    # ------------------------------------------------------------------

    def list_windows(self) -> list[dict]:
        """List open windows."""
        try:
            if PLATFORM == "linux":
                result = subprocess.run(
                    "wmctrl -l", shell=True, capture_output=True, text=True
                )
                windows = []
                for line in result.stdout.strip().splitlines():
                    parts = line.split(None, 3)
                    if len(parts) >= 4:
                        windows.append({"id": parts[0], "title": parts[3]})
                return windows

            elif PLATFORM == "windows":
                try:
                    import pygetwindow as gw
                    return [{"title": w.title} for w in gw.getAllWindows() if w.title]
                except ImportError:
                    pass

        except Exception as e:
            logger.error(f"List windows error: {e}")
        return []

    def list_running_apps(self) -> list[str]:
        """List names of running applications."""
        try:
            import psutil
            return list({p.name() for p in psutil.process_iter(["name"])})
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Common shortcuts
    # ------------------------------------------------------------------

    def open_browser(self, url: str = "") -> bool:
        """Open default browser, optionally to a URL."""
        if url:
            return self.open(f"xdg-open '{url}'" if PLATFORM == "linux" else url)
        return self.open("xdg-open" if PLATFORM == "linux" else "start")

    def open_terminal(self) -> bool:
        terminals = ["gnome-terminal", "xterm", "konsole", "xfce4-terminal"]
        for t in terminals:
            if self.open(t):
                return True
        return False

    def open_file_manager(self, path: str = "") -> bool:
        cmd = f"xdg-open '{path or os.path.expanduser('~')}'"
        return self.open(cmd)

    def lock_screen(self) -> bool:
        cmds = ["gnome-screensaver-command -l", "xdg-screensaver lock", "loginctl lock-session"]
        for cmd in cmds:
            result = subprocess.run(cmd, shell=True, capture_output=True)
            if result.returncode == 0:
                return True
        return False

    def take_screenshot(self, path: str = "/tmp/screenshot.png") -> bool:
        from senses.eyes import eyes
        return eyes.save_screenshot(path)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _log(self, action: str):
        try:
            from core.jarvis import jarvis
            if jarvis.memory:
                jarvis.memory.log_action(action)
        except Exception:
            pass

    def status(self) -> dict:
        return {
            "platform": PLATFORM,
            "open_windows": len(self.list_windows()),
            "running_apps": len(self.list_running_apps()),
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

apps = AppControl()
