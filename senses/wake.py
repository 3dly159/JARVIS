"""
senses/wake.py - JARVIS Wake Word + Hotkey Listener

Wake word detection via OpenWakeWord ("hey jarvis" — local, no API key, CPU).
Hotkey fallback via keyboard library (default: ctrl+space).

When triggered, calls on_wake(source) where source is "wake_word" or "hotkey".

Usage:
    from senses.wake import wake_listener
    wake_listener.start(on_wake=my_callback)
    wake_listener.stop()
"""

import logging
import threading
import time
import queue
import numpy as np
from typing import Any, Callable, Optional

logger = logging.getLogger("jarvis.wake")

# Audio config (OpenWakeWord expects 16kHz mono)
SAMPLE_RATE = 16000
CHUNK_DURATION = 0.08        # 80ms chunks — OWW default
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_DURATION)
DETECTION_THRESHOLD = 0.5    # Confidence threshold (0.0 - 1.0)
COOLDOWN_SECONDS = 2.0       # Ignore re-triggers for this long after wake


class WakeListener:
    """
    Listens for wake word ("hey jarvis") via OpenWakeWord
    and hotkey (ctrl+space) via keyboard library.
    Both trigger the same on_wake callback.
    """

    def __init__(
        self,
        wake_word: Any = "hey jarvis",
        hotkey: str = "ctrl+space",
        on_wake: Optional[Callable[[str], None]] = None,
        threshold: float = DETECTION_THRESHOLD,
    ):
        # Support list or comma-separated string
        if isinstance(wake_word, str):
            words = [w.strip() for w in wake_word.split(",")]
        elif isinstance(wake_word, list):
            words = wake_word
        else:
            words = ["hey jarvis"]

        # Map to specific OWW model names (e.g., hey_jarvis -> hey_jarvis_v0.1)
        self.wake_words = []
        for w in words:
            normalized = w.lower().replace(" ", "_")
            if normalized == "hey_jarvis":
                self.wake_words.append("hey_jarvis_v0.1")
            elif normalized == "hey_mycroft":
                self.wake_words.append("hey_mycroft_v0.1")
            elif normalized == "alexa":
                self.wake_words.append("alexa_v0.1")
            else:
                self.wake_words.append(normalized)

        self.hotkey = hotkey
        self.on_wake = on_wake
        self.threshold = threshold
        self.enabled = True

        self._running = False
        self._oww_thread: Optional[threading.Thread] = None
        self._last_triggered: float = 0.0
        self._oww_model = None

        logger.info(f"Wake listener ready. Wake words: {self.wake_words} | Hotkey: {hotkey}")

    # ------------------------------------------------------------------
    # Start / Stop
    # ------------------------------------------------------------------

    def start(self, on_wake: Optional[Callable] = None):
        """Start both wake word and hotkey listeners."""
        if self._running:
            logger.debug("Wake listener already running.")
            return

        if on_wake:
            self.on_wake = on_wake

        logger.info("Starting auditory sensors...")
        self._running = True
        self._start_oww()
        self._start_hotkey()
        logger.info("Wake listener fully active.")

    def stop(self):
        """Stop all listeners."""
        self._running = False
        self._stop_hotkey()
        logger.info("Wake listener stopped.")

    # ------------------------------------------------------------------
    # OpenWakeWord
    # ------------------------------------------------------------------

    def _load_oww_model(self) -> bool:
        """Load the OpenWakeWord model. Returns True on success."""
        try:
            from openwakeword.model import Model
            from openwakeword import get_pretrained_model_paths
            
            # Resolve absolute paths for the requested models
            all_paths = get_pretrained_model_paths()
            resolved_paths = []
            
            for w in self.wake_words:
                # Try finding a direct match or suffix match (e.g., hey_jarvis_v0.1.onnx)
                match = next((p for p in all_paths if w in p), None)
                if match:
                    resolved_paths.append(match)
                else:
                    logger.warning(f"Model '{w}' not found in resources. Skipping.")

            if not resolved_paths:
                logger.error("No valid wake word models found.")
                return False

            logger.info(f"Loading OpenWakeWord models: {resolved_paths}...")
            self._oww_model = Model(wakeword_model_paths=resolved_paths)
            logger.info("OpenWakeWord models loaded successfully.")
            return True
        except ImportError:
            logger.error("openwakeword not installed. Run: pip install openwakeword")
            return False
        except Exception as e:
            logger.warning(f"hey_jarvis model unavailable ({e}), trying default OWW models.")
            try:
                from openwakeword.model import Model
                self._oww_model = Model()
                logger.info("OpenWakeWord loaded with default models.")
                return True
            except Exception as e2:
                logger.error(f"OpenWakeWord failed to load: {e2}")
                return False

    def _start_oww(self):
        """Subscribe to the master mic bridge."""
        if not self._load_oww_model():
            logger.warning("Wake word detection unavailable — hotkey only.")
            return

        from senses.mic_bridge import mic_bridge
        mic_bridge.subscribe(self._on_audio_chunk)
        logger.info("Wake word listener subscribed to master mic stream.")

    def _on_audio_chunk(self, audio: np.ndarray):
        """Called by MicBridge with 80ms chunks of 16kHz audio."""
        if not self._running or not self.enabled:
            return

        try:
            # Feed to OWW
            prediction = self._oww_model.predict(audio)

            # Inhibit processing if JARVIS is currently speaking
            # This implements the "Patience Protocol" (No Interruption)
            from core.jarvis import jarvis
            if jarvis.voice and jarvis.voice.is_speaking:
                return

            # Standard Wake Word Threshold logic
            current_threshold = self.threshold
            
            for model_name, score in prediction.items():
                if score >= current_threshold:
                    self._trigger("wake_word")
                    break

        except Exception as e:
            logger.debug(f"OWW processing error: {e}")

    # ------------------------------------------------------------------
    # Hotkey
    # ------------------------------------------------------------------

    def _start_hotkey(self):
        """Register global hotkey."""
        import os, sys
        if sys.platform == "linux" and os.geteuid() != 0:
            logger.warning("Hotkey disabled: 'keyboard' library requires root (sudo) on Linux.")
            return

        try:
            import keyboard
            keyboard.add_hotkey(self.hotkey, lambda: self._trigger("hotkey"))
            logger.info(f"Hotkey registered: {self.hotkey}")
        except ImportError:
            logger.warning("keyboard library not installed. Run: pip install keyboard")
        except Exception as e:
            logger.warning(f"Hotkey registration failed: {e}")

    def _stop_hotkey(self):
        try:
            import keyboard
            keyboard.remove_hotkey(self.hotkey)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Trigger
    # ------------------------------------------------------------------

    def _trigger(self, source: str):
        """Called when wake word or hotkey fires."""
        if not self.enabled:
            return

        # Cooldown: ignore rapid re-triggers
        now = time.time()
        if now - self._last_triggered < COOLDOWN_SECONDS:
            return
        self._last_triggered = now

        logger.info(f"Wake triggered via {source}.")
        
        # Interruption logic: If JARVIS is speaking, stop him.
        try:
            from core.jarvis import jarvis
            if jarvis.voice and jarvis.voice.is_speaking:
                logger.info("Interruption detected! Silencing system.")
                jarvis.interrupt()
                # We still trigger on_wake so that it starts a NEW listen cycle
        except Exception as e:
            logger.debug(f"Interruption check failed: {e}")

        if self.on_wake:
            threading.Thread(
                target=self.on_wake,
                args=(source,),
                daemon=True,
            ).start()

    # ------------------------------------------------------------------
    # Hotkey update
    # ------------------------------------------------------------------

    def update_hotkey(self, new_hotkey: str):
        """Change hotkey at runtime (hot-reload support)."""
        self._stop_hotkey()
        self.hotkey = new_hotkey
        self._start_hotkey()
        logger.info(f"Hotkey updated: {new_hotkey}")

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def status(self) -> dict:
        return {
            "wake_words": self.wake_words,
            "hotkey": self.hotkey,
            "enabled": self.enabled,
            "running": self._running,
            "oww_loaded": self._oww_model is not None,
            "threshold": self.threshold,
            "cooldown_seconds": COOLDOWN_SECONDS,
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

from core.config_manager import config

wake_listener = WakeListener(
    wake_word=config.get("voice.wake_word", "hey jarvis"),
    hotkey=config.get("voice.hotkey", "ctrl+space"),
    threshold=DETECTION_THRESHOLD,
)

# Hot-reload hotkey when config changes
config.on_change(
    "voice",
    lambda key, old, new: wake_listener.update_hotkey(config.get("voice.hotkey"))
    if key == "voice.hotkey" else None,
)


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Testing wake listener...\n")
    print("Say 'Hey JARVIS' or press Ctrl+Space. Ctrl+C to exit.\n")

    def on_wake(source):
        print(f"\n🟢 WAKE TRIGGERED via {source}!")

    wake_listener.start(on_wake=on_wake)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        wake_listener.stop()
        print("\nStopped.")
