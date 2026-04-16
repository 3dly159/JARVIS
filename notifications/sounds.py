"""
notifications/sounds.py - JARVIS Sound Alerts

Simple audio alerts for different notification priorities.
Uses sounddevice + numpy to generate tones (no audio files needed).
"""

import logging
import threading
import numpy as np
from typing import Optional

logger = logging.getLogger("jarvis.sounds")

# Tone definitions: (frequency_hz, duration_s, volume)
TONES = {
    "info":    [(880, 0.1, 0.3)],
    "warning": [(660, 0.15, 0.5), (440, 0.15, 0.5)],
    "urgent":  [(880, 0.1, 0.7), (880, 0.1, 0.7), (880, 0.1, 0.7)],
    "wake":    [(1047, 0.08, 0.4), (1319, 0.12, 0.4)],
    "online":  [(523, 0.1, 0.3), (659, 0.1, 0.3), (784, 0.2, 0.4)],
    "offline": [(784, 0.1, 0.3), (659, 0.1, 0.3), (523, 0.2, 0.4)],
}

SAMPLE_RATE = 44100


class Sounds:
    """Generate and play simple tones for notifications."""

    def __init__(self):
        self._available = self._check()

    def _check(self) -> bool:
        try:
            import sounddevice
            import numpy
            return True
        except ImportError:
            logger.debug("sounddevice/numpy not available — sounds disabled.")
            return False

    def _generate_tone(self, freq: float, duration: float, volume: float = 0.5) -> np.ndarray:
        """Generate a sine wave tone."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        # Fade in/out to avoid clicks
        fade = int(SAMPLE_RATE * 0.01)
        wave = volume * np.sin(2 * np.pi * freq * t)
        if len(wave) > fade * 2:
            wave[:fade] *= np.linspace(0, 1, fade)
            wave[-fade:] *= np.linspace(1, 0, fade)
        return wave.astype(np.float32)

    def play(self, sound_name: str):
        """Play a named sound in background thread."""
        if not self._available:
            return
        if sound_name not in TONES:
            logger.debug(f"Unknown sound: {sound_name}")
            return
        threading.Thread(
            target=self._play_tones,
            args=(TONES[sound_name],),
            daemon=True,
        ).start()

    def _play_tones(self, tones: list):
        try:
            import sounddevice as sd
            for freq, duration, volume in tones:
                wave = self._generate_tone(freq, duration, volume)
                sd.play(wave, SAMPLE_RATE)
                sd.wait()
        except Exception as e:
            logger.debug(f"Sound play error: {e}")

    def play_tone(self, freq: float, duration: float = 0.2, volume: float = 0.4):
        """Play a custom tone."""
        if not self._available:
            return
        threading.Thread(
            target=self._play_tones,
            args=([(freq, duration, volume)],),
            daemon=True,
        ).start()

    def status(self) -> dict:
        return {
            "available": self._available,
            "sounds": list(TONES.keys()),
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

sounds = Sounds()
