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
import numpy as np
import soundfile as sf
import sounddevice as sd
from datetime import datetime
from pathlib import Path
from typing import Optional

from senses.mic_bridge import mic_bridge

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
        quiet_hours_enabled: bool = False,
    ):
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self.volume = volume
        self.quiet_start = quiet_start
        self.quiet_end = quiet_end
        self.quiet_hours_enabled = quiet_hours_enabled
        self.enabled = True
        self.muted = False
        self.is_speaking = False
        self.on_finished: Optional[Callable[[], None]] = None

        self._queue: queue.Queue = queue.Queue()
        self._worker_thread = threading.Thread(target=self._worker, daemon=True, name="voice-worker")
        self._worker_thread.start()
        logger.info(f"Voice engine worker thread online.")
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
        if self.quiet_hours_enabled and self._is_quiet_hours():
            logger.info(f"Vocal response suppressed (Quiet Hours): {text[:60]}...")
            return

        if priority:
            # Clear queue for urgent messages
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break

        self._queue.put(text)
        logger.info(f"Vocal directive queued: {text[:60]}...")

    def stop(self):
        """Immediately stop playback and clear the queue."""
        import sounddevice as sd
        try:
            sd.stop()
        except Exception:
            pass
        
        # Clear queue
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
        
        self.is_speaking = False
        logger.info("Voice playback stopped and queue cleared.")

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
        if "quiet_hours_enabled" in settings:
            self.quiet_hours_enabled = settings["quiet_hours_enabled"]
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
            
            # Record playback start
            logger.info(f"Vocalizing: {text[:60]}...")

            # Play audio
            data, samplerate = sf.read(tmp_path)
            
            # 1. Calculate and set expected volume baseline FIRST
            try:
                rms = float(np.sqrt(np.mean(data**2)))
                # Normalize and scale if needed (optional)
                mic_bridge.expected_speaker_rms = rms
                logger.info(f"Vocal baseline set: {rms:.4f}")
            except Exception as e:
                logger.warning(f"RMS calculation failed: {e}")

            # 2. Now set the flag that ears.py is watching
            self.is_speaking = True
            
            # Broadcast state to UI
            try:
                from core.jarvis import jarvis
                jarvis._broadcast_state("speaking")
            except Exception: pass

            sd.play(data, samplerate)
            
            # Use a slightly more robust waiting logic
            while sd.get_stream().active:
                time.sleep(0.05)
            
            # Reset baseline
            try:
                mic_bridge.expected_speaker_rms = 0.0
            except Exception: pass
            
            self.is_speaking = False
            logger.info("Vocalization complete.")
            os.unlink(tmp_path)
            
            # Trigger finished callback
            if self.on_finished:
                try:
                    self.on_finished()
                except Exception as e:
                    logger.error(f"Voice finished callback error: {e}")

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
            "quiet_hours_enabled": self.quiet_hours_enabled,
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
    quiet_hours_enabled=config.get("notifications.quiet_hours_enabled", True),
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
