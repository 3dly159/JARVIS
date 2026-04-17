"""
core/config_manager.py - JARVIS Config Manager

Single source of truth for all configuration.
Hot-reloads config.yaml when it changes on disk.
All modules read from here — never hardcode values.

Usage:
    from core.config_manager import config
    model = config.get("llm.model")
    config.set("llm.temperature", 0.8)   # writes to config.yaml
    config.on_change("llm", my_callback) # called when llm section changes
"""

import logging
import threading
import time
import yaml
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger("jarvis.config")

ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "config.yaml"

# ---------------------------------------------------------------------------
# Defaults (used if config.yaml is missing or key absent)
# ---------------------------------------------------------------------------

DEFAULTS = {
    "llm": {
        "model": "gemma4:latest",
        "ollama_host": "http://localhost:11434",
        "temperature": 0.7,
        "context_window": 16384,
    },
    "voice": {
        "tts_engine": "edge-tts",
        "tts_voice": "en-GB-RyanNeural",
        "tts_rate": "+0%",
        "tts_pitch": "+0Hz",
        "stt_model": "base.en",
        "stt_device": "cuda",
        "wake_word": "hey jarvis",
        "hotkey": "ctrl+space",
    },
    "ui": {
        "host": "127.0.0.1",
        "port": 8090,
        "open_browser_on_start": True,
    },
    "agents": {
        "max_agents": 20,
        "max_parallel": 5,
    },
    "memory": {
        "daily_log_dir": "memory/",
        "palace_dir": "memory/palace/",
        "summarize_after_days": 7,
    },
    "monitor": {
        "enabled": True,
        "check_interval_seconds": 30,
        "cpu_alert_threshold": 90,
        "ram_alert_threshold": 85,
        "vram_alert_threshold": 90,
    },
    "tasks": {
        "self_ping_interval_seconds": 60,
        "stall_threshold_minutes": 10,
    },
    "actions": {
        "require_confirmation": ["shell_command", "file_delete", "keyboard_mouse"],
        "confirmation_timeout_seconds": 30,
    },
    "self_mod": {
        "enabled": True,
        "sandbox_before_apply": True,
        "backup_on_modify": True,
    },
    "notifications": {
        "tray_enabled": True,
        "voice_alerts": True,
        "quiet_hours_start": "23:00",
        "quiet_hours_end": "08:00",
    },
    "logging": {
        "level": "INFO",
        "log_dir": "logs/",
        "log_conversations": True,
    },
}


# ---------------------------------------------------------------------------
# Config Manager
# ---------------------------------------------------------------------------

class ConfigManager:
    """
    Hot-reloading config manager.
    Reads config.yaml, merges with defaults, watches for file changes.
    """

    def __init__(self, config_path: Path = CONFIG_PATH):
        self._path = config_path
        self._data: dict = {}
        self._lock = threading.RLock()
        self._callbacks: dict[str, list[Callable]] = {}  # section → callbacks
        self._watch_thread: Optional[threading.Thread] = None
        self._running = False
        self._last_mtime: float = 0.0
        self._load()
        logger.info("Config manager online.")

    # ------------------------------------------------------------------
    # Load / Save
    # ------------------------------------------------------------------

    def _load(self):
        """Load config.yaml and merge with defaults."""
        with self._lock:
            file_data = {}
            if self._path.exists():
                try:
                    with self._path.open(encoding="utf-8") as f:
                        file_data = yaml.safe_load(f) or {}
                    self._last_mtime = self._path.stat().st_mtime
                    logger.debug(f"Config loaded from {self._path.name}")
                except Exception as e:
                    logger.error(f"Failed to load config: {e}")

            # Deep merge: defaults ← file_data
            self._data = self._deep_merge(DEFAULTS, file_data)

    def _save(self):
        """Write current config to config.yaml."""
        with self._lock:
            try:
                with self._path.open("w", encoding="utf-8") as f:
                    yaml.dump(self._data, f, default_flow_style=False, allow_unicode=True)
                self._last_mtime = self._path.stat().st_mtime
                logger.info("Config saved.")
            except Exception as e:
                logger.error(f"Failed to save config: {e}")

    def _deep_merge(self, base: dict, override: dict) -> dict:
        """Recursively merge override into base."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    # ------------------------------------------------------------------
    # Get / Set
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a config value by dot-path key.
        e.g. config.get("llm.model") or config.get("voice.tts_voice")
        """
        with self._lock:
            parts = key.split(".")
            data = self._data
            for part in parts:
                if isinstance(data, dict) and part in data:
                    data = data[part]
                else:
                    return default
            return data

    def set(self, key: str, value: Any, save: bool = True):
        """
        Set a config value by dot-path key. Persists to disk by default.
        e.g. config.set("llm.temperature", 0.9)
        Triggers on_change callbacks for the affected section.
        """
        with self._lock:
            parts = key.split(".")
            data = self._data
            for part in parts[:-1]:
                data = data.setdefault(part, {})
            old_value = data.get(parts[-1])
            data[parts[-1]] = value

            if save:
                self._save()

            # Fire callbacks for top-level section
            section = parts[0]
            if old_value != value:
                self._fire_callbacks(section, key, old_value, value)

        logger.info(f"Config updated: {key} = {value}")

    def section(self, name: str) -> dict:
        """Get an entire config section as a dict."""
        with self._lock:
            return self._data.get(name, DEFAULTS.get(name, {})).copy()

    def all(self) -> dict:
        """Get full config as dict."""
        with self._lock:
            return self._data.copy()

    # ------------------------------------------------------------------
    # Change callbacks
    # ------------------------------------------------------------------

    def on_change(self, section: str, callback: Callable):
        """
        Register a callback for when a config section changes.
        callback(key, old_value, new_value)
        """
        if section not in self._callbacks:
            self._callbacks[section] = []
        self._callbacks[section].append(callback)

    def _fire_callbacks(self, section: str, key: str, old: Any, new: Any):
        for cb in self._callbacks.get(section, []):
            try:
                cb(key, old, new)
            except Exception as e:
                logger.error(f"Config callback error [{section}]: {e}")

    # ------------------------------------------------------------------
    # File watcher (hot-reload)
    # ------------------------------------------------------------------

    def start_watching(self):
        """Start watching config.yaml for external changes."""
        if self._running:
            return
        self._running = True
        self._watch_thread = threading.Thread(
            target=self._watch_loop, daemon=True, name="config-watcher"
        )
        self._watch_thread.start()
        logger.info("Config file watcher started.")

    def stop_watching(self):
        self._running = False

    def _watch_loop(self):
        while self._running:
            time.sleep(2)
            try:
                if not self._path.exists():
                    continue
                mtime = self._path.stat().st_mtime
                if mtime != self._last_mtime:
                    logger.info("config.yaml changed on disk — hot-reloading.")
                    old_data = self._data.copy()
                    self._load()
                    self._diff_and_fire(old_data, self._data)
            except Exception as e:
                logger.error(f"Config watcher error: {e}")

    def _diff_and_fire(self, old: dict, new: dict):
        """Compare old and new config, fire callbacks for changed sections."""
        for section in set(list(old.keys()) + list(new.keys())):
            if old.get(section) != new.get(section):
                logger.info(f"Config section changed: {section}")
                for cb in self._callbacks.get(section, []):
                    try:
                        cb(section, old.get(section), new.get(section))
                    except Exception as e:
                        logger.error(f"Config reload callback error: {e}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def reload(self):
        """Force reload from disk."""
        old = self._data.copy()
        self._load()
        self._diff_and_fire(old, self._data)
        logger.info("Config reloaded.")

    def reset_to_defaults(self):
        """Reset to built-in defaults and save."""
        with self._lock:
            self._data = DEFAULTS.copy()
            self._save()
        logger.info("Config reset to defaults.")


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

config = ConfigManager()
config.start_watching()


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print("Config manager test\n")

    print("LLM model:", config.get("llm.model"))
    print("TTS voice:", config.get("voice.tts_voice"))
    print("UI port:  ", config.get("ui.port"))
    print("Max agents:", config.get("agents.max_agents"))

    # Test set
    config.set("llm.temperature", 0.9, save=False)
    print("\nUpdated temperature:", config.get("llm.temperature"))

    # Test callback
    def on_llm_change(key, old, new):
        print(f"  → LLM config changed: {key}: {old} → {new}")

    config.on_change("llm", on_llm_change)
    config.set("llm.temperature", 0.5, save=False)
