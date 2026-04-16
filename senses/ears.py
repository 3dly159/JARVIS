"""
senses/ears.py - JARVIS Ears (STT)

Speech-to-text via faster-whisper (local, CUDA-accelerated).
Supports continuous listening, one-shot capture, and push-to-talk.

Usage:
    from senses.ears import ears
    text = ears.listen_once()           # block until speech captured
    ears.start_continuous(callback)     # background listening
    ears.stop_continuous()
"""

import logging
import queue
import threading
import time
import numpy as np
from typing import Optional, Callable

logger = logging.getLogger("jarvis.ears")

# Audio config
SAMPLE_RATE = 16000      # Hz — Whisper expects 16kHz
CHANNELS = 1             # Mono
CHUNK_DURATION = 0.5     # seconds per audio chunk
SILENCE_THRESHOLD = 0.01 # RMS below this = silence
SILENCE_DURATION = 1.5   # seconds of silence = end of utterance
MAX_RECORD_SECONDS = 30  # max single utterance length


class Ears:
    """
    JARVIS STT via faster-whisper.
    Captures mic audio, detects speech, transcribes locally.
    """

    def __init__(
        self,
        model_size: str = "base.en",
        device: str = "cuda",
        compute_type: str = "float16",
        language: str = "en",
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self._model = None
        self._continuous = False
        self._continuous_thread: Optional[threading.Thread] = None
        self._callback: Optional[Callable] = None
        self._load_model()

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def _load_model(self):
        try:
            from faster_whisper import WhisperModel
            logger.info(f"Loading Whisper model: {self.model_size} on {self.device}...")

            # Fallback to CPU + int8 if CUDA unavailable
            try:
                self._model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                )
                logger.info(f"Whisper loaded on {self.device}.")
            except Exception:
                logger.warning("CUDA unavailable — falling back to CPU.")
                self._model = WhisperModel(
                    self.model_size,
                    device="cpu",
                    compute_type="int8",
                )
                logger.info("Whisper loaded on CPU.")

        except ImportError:
            logger.error("faster-whisper not installed. Run: pip install faster-whisper")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")

    # ------------------------------------------------------------------
    # Audio capture
    # ------------------------------------------------------------------

    def _capture_utterance(self, timeout: float = 10.0) -> Optional[np.ndarray]:
        """
        Record a single utterance from the microphone.
        Starts when speech is detected, ends after silence.
        Returns numpy float32 array at 16kHz, or None on timeout/error.
        """
        try:
            import sounddevice as sd
        except ImportError:
            logger.error("sounddevice not installed. Run: pip install sounddevice")
            return None

        chunk_samples = int(SAMPLE_RATE * CHUNK_DURATION)
        audio_chunks = []
        silent_chunks = 0
        silent_limit = int(SILENCE_DURATION / CHUNK_DURATION)
        max_chunks = int(MAX_RECORD_SECONDS / CHUNK_DURATION)
        speech_started = False
        start_time = time.time()

        logger.debug("Listening for speech...")

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            blocksize=chunk_samples,
        ) as stream:
            while True:
                # Timeout check
                if time.time() - start_time > timeout:
                    logger.debug("Listen timeout reached.")
                    break

                chunk, _ = stream.read(chunk_samples)
                chunk_flat = chunk.flatten()
                rms = float(np.sqrt(np.mean(chunk_flat ** 2)))

                if rms > SILENCE_THRESHOLD:
                    # Speech detected
                    if not speech_started:
                        logger.debug("Speech started.")
                        speech_started = True
                    audio_chunks.append(chunk_flat)
                    silent_chunks = 0
                else:
                    if speech_started:
                        silent_chunks += 1
                        audio_chunks.append(chunk_flat)  # include trailing silence
                        if silent_chunks >= silent_limit:
                            logger.debug("Speech ended (silence detected).")
                            break
                    # If no speech yet, don't accumulate silence

                # Hard limit
                if len(audio_chunks) >= max_chunks:
                    logger.debug("Max recording length reached.")
                    break

        if not audio_chunks or not speech_started:
            return None

        return np.concatenate(audio_chunks)

    # ------------------------------------------------------------------
    # Transcription
    # ------------------------------------------------------------------

    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe a numpy audio array to text."""
        if self._model is None:
            logger.error("Whisper model not loaded.")
            return ""
        try:
            segments, info = self._model.transcribe(
                audio,
                language=self.language,
                beam_size=5,
                vad_filter=True,          # filter out non-speech
                vad_parameters={"min_silence_duration_ms": 500},
            )
            text = " ".join(s.text.strip() for s in segments).strip()
            logger.info(f"Transcribed: '{text}'")
            return text
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""

    # ------------------------------------------------------------------
    # Listen once
    # ------------------------------------------------------------------

    def listen_once(
        self,
        timeout: float = 10.0,
        callback: Optional[Callable[[str], None]] = None,
    ) -> str:
        """
        Listen for one utterance and return the transcription.
        If callback provided, calls it with the text instead.
        Blocks until utterance captured or timeout.
        """
        audio = self._capture_utterance(timeout=timeout)
        if audio is None:
            text = ""
        else:
            text = self.transcribe(audio)

        if callback and text:
            callback(text)

        return text

    # ------------------------------------------------------------------
    # Continuous listening
    # ------------------------------------------------------------------

    def start_continuous(self, callback: Callable[[str], None]):
        """
        Start background continuous listening.
        Calls callback(text) whenever speech is detected and transcribed.
        """
        if self._continuous:
            logger.warning("Continuous listening already running.")
            return

        self._continuous = True
        self._callback = callback
        self._continuous_thread = threading.Thread(
            target=self._continuous_loop,
            daemon=True,
            name="ears-continuous",
        )
        self._continuous_thread.start()
        logger.info("Continuous listening started.")

    def stop_continuous(self):
        """Stop background continuous listening."""
        self._continuous = False
        logger.info("Continuous listening stopped.")

    def _continuous_loop(self):
        """Background loop: listen → transcribe → callback → repeat."""
        while self._continuous:
            try:
                audio = self._capture_utterance(timeout=5.0)
                if audio is not None:
                    text = self.transcribe(audio)
                    if text and self._callback:
                        self._callback(text)
            except Exception as e:
                logger.error(f"Continuous listen error: {e}")
                time.sleep(1)

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def status(self) -> dict:
        return {
            "model_size": self.model_size,
            "device": self.device,
            "model_loaded": self._model is not None,
            "continuous": self._continuous,
            "language": self.language,
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

from core.config_manager import config

ears = Ears(
    model_size=config.get("voice.stt_model", "base.en"),
    device=config.get("voice.stt_device", "cuda"),
)


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Testing JARVIS ears (Whisper STT)...\n")
    print("Speak now (up to 10 seconds)...")
    text = ears.listen_once(timeout=10.0)
    if text:
        print(f"\nTranscribed: '{text}'")
    else:
        print("\nNo speech detected.")
    print("\nStatus:", ears.status())
