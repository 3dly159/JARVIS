"""
system/startup.py - JARVIS Startup Manager

Handles autostart, background service, and tray icon.
Manages JARVIS as a persistent background process.

Usage:
    from system.startup import startup
    startup.enable_autostart()
    startup.disable_autostart()
    startup.is_autostart_enabled()
"""

import logging
import os
import platform
import subprocess
from pathlib import Path

logger = logging.getLogger("jarvis.startup")

PLATFORM = platform.system().lower()
ROOT = Path(__file__).parent.parent
MAIN_SCRIPT = ROOT / "main.py"


class StartupManager:
    """Manage JARVIS autostart at system boot."""

    # ------------------------------------------------------------------
    # Autostart
    # ------------------------------------------------------------------

    def enable_autostart(self) -> bool:
        """Enable JARVIS to start automatically at login."""
        try:
            if PLATFORM == "linux":
                return self._enable_linux()
            elif PLATFORM == "windows":
                return self._enable_windows()
            elif PLATFORM == "darwin":
                return self._enable_macos()
            logger.warning(f"Autostart not supported on {PLATFORM}")
            return False
        except Exception as e:
            logger.error(f"Enable autostart error: {e}")
            return False

    def disable_autostart(self) -> bool:
        """Disable JARVIS autostart."""
        try:
            if PLATFORM == "linux":
                return self._disable_linux()
            elif PLATFORM == "windows":
                return self._disable_windows()
            elif PLATFORM == "darwin":
                return self._disable_macos()
            return False
        except Exception as e:
            logger.error(f"Disable autostart error: {e}")
            return False

    def is_autostart_enabled(self) -> bool:
        if PLATFORM == "linux":
            return self._get_linux_autostart_path().exists()
        elif PLATFORM == "windows":
            return self._check_windows_registry()
        elif PLATFORM == "darwin":
            return self._get_macos_plist_path().exists()
        return False

    # ------------------------------------------------------------------
    # Linux (XDG autostart)
    # ------------------------------------------------------------------

    def _get_linux_autostart_path(self) -> Path:
        xdg_config = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        return xdg_config / "autostart" / "jarvis.desktop"

    def _enable_linux(self) -> bool:
        path = self._get_linux_autostart_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        python = subprocess.check_output(["which", "python3"]).decode().strip()
        content = f"""[Desktop Entry]
Type=Application
Name=JARVIS
Comment=Just A Rather Very Intelligent System
Exec={python} {MAIN_SCRIPT}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
        path.write_text(content)
        logger.info(f"Autostart enabled: {path}")
        return True

    def _disable_linux(self) -> bool:
        path = self._get_linux_autostart_path()
        if path.exists():
            path.unlink()
            logger.info("Autostart disabled.")
        return True

    # ------------------------------------------------------------------
    # Windows (Registry)
    # ------------------------------------------------------------------

    def _check_windows_registry(self) -> bool:
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Run")
            winreg.QueryValueEx(key, "JARVIS")
            return True
        except Exception:
            return False

    def _enable_windows(self) -> bool:
        try:
            import winreg
            python = subprocess.check_output(["where", "python"]).decode().strip().splitlines()[0]
            cmd = f'"{python}" "{MAIN_SCRIPT}"'
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Run",
                                 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "JARVIS", 0, winreg.REG_SZ, cmd)
            logger.info("Autostart enabled (Windows registry).")
            return True
        except Exception as e:
            logger.error(f"Windows autostart error: {e}")
            return False

    def _disable_windows(self) -> bool:
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Run",
                                 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, "JARVIS")
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # macOS (LaunchAgent)
    # ------------------------------------------------------------------

    def _get_macos_plist_path(self) -> Path:
        return Path.home() / "Library" / "LaunchAgents" / "ai.jarvis.plist"

    def _enable_macos(self) -> bool:
        python = subprocess.check_output(["which", "python3"]).decode().strip()
        plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
"http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>ai.jarvis</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python}</string>
        <string>{MAIN_SCRIPT}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>"""
        path = self._get_macos_plist_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(plist)
        subprocess.run(["launchctl", "load", str(path)], capture_output=True)
        logger.info(f"Autostart enabled (macOS): {path}")
        return True

    def _disable_macos(self) -> bool:
        path = self._get_macos_plist_path()
        if path.exists():
            subprocess.run(["launchctl", "unload", str(path)], capture_output=True)
            path.unlink()
        return True

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def status(self) -> dict:
        return {
            "platform": PLATFORM,
            "autostart_enabled": self.is_autostart_enabled(),
            "main_script": str(MAIN_SCRIPT),
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

startup = StartupManager()
