"""
senses/voice.py - JARVIS Voice (TTS)

Text-to-speech via Microsoft Edge TTS.
Non-blocking queue-based output. Respects quiet hours.
Voice: en-GB-RyanNeural (British male — closest to MCU JARVIS)

Usage:
    from senses.voice import voice
    voice.speak("Good evening, sir.")
    voice.speak_async("Processing...")  # fire and forget
"""

import asyncio
import logging
import queue
import threading
import time
import tempfile
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("jarvis.voice")


class Voice:
    """
    Edge TTS wrapper with non-blocking queue.
    Speak calls return immediately; audio plays in background thread.
    """

    def __init__(
        self,
        voice: str = "en-GB-RyanNeural",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        quiet_start: str = "23:00",
        quiet_end: str = "08:00",
        volume: str = "+0%",
    ):
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self.volume = volume
        self.quiet_start = quiet_start
        self.quiet_end = quiet_end
        self.enabled = True
        self.muted = False

        self._queue: queue.Queue = queue.Queue()
        self._worker_thread = threading.Thread(target=self._worker, daemon=True, name="voice-worker")
        self._worker_thread.start()
        logger.info(f"Voice online. Voice: {voice}, Rate: {rate}")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def speak(self, text: str, priority: bool = False):
        """
        Queue text for speaking. Returns immediately.
        priority=True clears the queue first (urgent messages).
        """
        if not text or not text.strip():
            return
        if self.muted or not self.enabled:
            logger.debug(f"Voice muted/disabled. Would say: {text[:60]}")
            return
        if self._is_quiet_hours():
            logger.debug(f"Quiet hours. Suppressing: {text[:60]}")
            return

        if priority:
            # Clear queue for urgent messages
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break

        self._queue.put(text)
        logger.debug(f"Queued: {text[:60]}")

    def speak_now(self, text: str):
        """Speak immediately, blocking until done. Bypasses queue."""
        if not text or not text.strip():
            return
        asyncio.run(self._synthesize_and_play(text))

    def mute(self):
        self.muted = True
        logger.info("Voice muted.")

    def unmute(self):
        self.muted = False
        logger.info("Voice unmuted.")

    def update(self, settings: dict):
        """Hot-reload voice settings from config."""
        if "tts_voice" in settings:
            self.voice = settings["tts_voice"]
        if "tts_rate" in settings:
            self.rate = settings["tts_rate"]
        if "tts_pitch" in settings:
            self.pitch = settings["tts_pitch"]
        if "quiet_hours_start" in settings:
            self.quiet_start = settings["quiet_hours_start"]
        if "quiet_hours_end" in settings:
            self.quiet_end = settings["quiet_hours_end"]
        logger.info(f"Voice settings updated: {settings}")

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _worker(self):
        """Background thread: pulls from queue and speaks."""
        while True:
            try:
                text = self._queue.get(timeout=1)
                asyncio.run(self._synthesize_and_play(text))
                self._queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Voice worker error: {e}")

    async def _synthesize_and_play(self, text: str):
        """Synthesize text to audio and play it."""
        try:
            import edge_tts
            import sounddevice as sd
            import soundfile as sf

            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice,
                rate=self.rate,
                pitch=self.pitch,
                volume=self.volume,
            )

            # Write to temp file then play
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name

            await communicate.save(tmp_path)

            # Play audio
            data, samplerate = sf.read(tmp_path)
            sd.play(data, samplerate)
            sd.wait()

            os.unlink(tmp_path)

        except ImportError as e:
            logger.error(f"Missing dependency: {e}. Install: pip install edge-tts sounddevice soundfile")
        except Exception as e:
            logger.error(f"TTS error: {e}")

    def _is_quiet_hours(self) -> bool:
        """Returns True if current time is within quiet hours."""
        try:
            now = datetime.now().strftime("%H:%M")
            start = self.quiet_start
            end = self.quiet_end

            if start <= end:
                return start <= now <= end
            else:
                # Wraps midnight e.g. 23:00 → 08:00
                return now >= start or now <= end
        except Exception:
            return False

    def status(self) -> dict:
        return {
            "voice": self.voice,
            "rate": self.rate,
            "pitch": self.pitch,
            "enabled": self.enabled,
            "muted": self.muted,
            "queue_size": self._queue.qsize(),
            "quiet_hours": f"{self.quiet_start} - {self.quiet_end}",
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

from core.config_manager import config

voice = Voice(
    voice=config.get("voice.tts_voice", "en-GB-RyanNeural"),
    rate=config.get("voice.tts_rate", "+0%"),
    pitch=config.get("voice.tts_pitch", "+0Hz"),
    quiet_start=config.get("notifications.quiet_hours_start", "23:00"),
    quiet_end=config.get("notifications.quiet_hours_end", "08:00"),
)


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Testing JARVIS voice...\n")
    print("Speaking: 'Good evening, sir. J.A.R.V.I.S. online.'")
    voice.speak_now("Good evening, sir. J.A.R.V.I.S. online.")
    print("Speaking: 'All systems are operational.'")
    voice.speak_now("All systems are operational.")
    print("\nStatus:", voice.status())
