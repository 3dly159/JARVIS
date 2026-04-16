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
from typing import Callable, Optional

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
        wake_word: str = "hey jarvis",
        hotkey: str = "ctrl+space",
        on_wake: Optional[Callable[[str], None]] = None,
        threshold: float = DETECTION_THRESHOLD,
    ):
        self.wake_word = wake_word
        self.hotkey = hotkey
        self.on_wake = on_wake
        self.threshold = threshold
        self.enabled = True

        self._running = False
        self._oww_thread: Optional[threading.Thread] = None
        self._last_triggered: float = 0.0
        self._oww_model = None

        logger.info(f"Wake listener ready. Wake word: '{wake_word}' | Hotkey: {hotkey}")

    # ------------------------------------------------------------------
    # Start / Stop
    # ------------------------------------------------------------------

    def start(self, on_wake: Optional[Callable] = None):
        """Start both wake word and hotkey listeners."""
        if on_wake:
            self.on_wake = on_wake
        if self._running:
            logger.warning("Wake listener already running.")
            return

        self._running = True
        self._start_oww()
        self._start_hotkey()
        logger.info("Wake listener started.")

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

            # OWW has a built-in "hey_jarvis" model — use it directly
            # If not available, it falls back to the nearest match
            self._oww_model = Model(
                wakeword_models=["hey_jarvis"],
                inference_framework="onnx",
            )
            logger.info("OpenWakeWord model loaded (hey_jarvis).")
            return True
        except ImportError:
            logger.error("openwakeword not installed. Run: pip install openwakeword")
            return False
        except Exception as e:
            # Model might not include hey_jarvis — try default
            logger.warning(f"hey_jarvis model unavailable ({e}), trying default OWW models.")
            try:
                from openwakeword.model import Model
                self._oww_model = Model(inference_framework="onnx")
                logger.info("OpenWakeWord loaded with default models.")
                return True
            except Exception as e2:
                logger.error(f"OpenWakeWord failed to load: {e2}")
                return False

    def _start_oww(self):
        """Start OpenWakeWord listener in background thread."""
        if not self._load_oww_model():
            logger.warning("Wake word detection unavailable — hotkey only.")
            return

        self._oww_thread = threading.Thread(
            target=self._oww_loop,
            daemon=True,
            name="wake-oww",
        )
        self._oww_thread.start()

    def _oww_loop(self):
        """Continuously feed mic audio to OpenWakeWord."""
        try:
            import sounddevice as sd
        except ImportError:
            logger.error("sounddevice not installed.")
            return

        logger.info("Wake word listener active. Say 'Hey JARVIS'...")

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=CHUNK_SAMPLES,
        ) as stream:
            while self._running:
                try:
                    chunk, _ = stream.read(CHUNK_SAMPLES)
                    audio = chunk.flatten()

                    # Feed to OWW
                    prediction = self._oww_model.predict(audio)

                    # Check all models for threshold crossing
                    for model_name, score in prediction.items():
                        if score >= self.threshold:
                            self._trigger("wake_word")
                            break

                except Exception as e:
                    if self._running:
                        logger.error(f"OWW loop error: {e}")
                    time.sleep(0.1)

    # ------------------------------------------------------------------
    # Hotkey
    # ------------------------------------------------------------------

    def _start_hotkey(self):
        """Register global hotkey."""
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
            "wake_word": self.wake_word,
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
