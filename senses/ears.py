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

import asyncio, logging, queue, threading, time, inspect
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
        
        # Interruption and Interaction tracking
        self._last_interaction_time = 0.0
        self._interruption_thread: Optional[threading.Thread] = None
        self._interruption_active = False
        self.start_interruption_monitor()

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

        from senses.mic_bridge import mic_bridge
        audio_queue = queue.Queue()
        LISTEN_GUARD_SECONDS = 0.5  # Ignore first 500ms to avoid echo

        def queue_callback(chunk):
            chunk_flat = chunk.astype(np.float32) / 32768.0
            audio_queue.put(chunk_flat)

        mic_bridge.subscribe(queue_callback)
        
        # Broadcast state
        try:
            from core.jarvis import jarvis
            jarvis._broadcast_state("listening")
        except Exception: pass
        
        try:
            while True:
                # Timeout check
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    logger.debug("Listen timeout reached.")
                    break

                try:
                    chunk_flat = audio_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Silence Guard: Discard chunks at the very beginning
                if elapsed < LISTEN_GUARD_SECONDS:
                    continue
                
                # Dynamic VAD: Raise the floor if JARVIS is talking
                # This prevents transcribing own echo
                current_silence_threshold = SILENCE_THRESHOLD
                expected_rms = mic_bridge.expected_speaker_rms
                if expected_rms > 0:
                    # Require signal to be at least 1.5x louder than speaker output
                    current_silence_threshold = max(current_silence_threshold, expected_rms * 1.5)

                rms = float(np.sqrt(np.mean(chunk_flat ** 2)))

                if rms > current_silence_threshold:
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
        finally:
            mic_bridge.unsubscribe(queue_callback)

        if not audio_chunks or not speech_started:
            return None

        return np.concatenate(audio_chunks)

    # ------------------------------------------------------------------
    # Transcription
    # ------------------------------------------------------------------

    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio chunk via faster-whisper."""
        try:
            from core.jarvis import jarvis
            jarvis._broadcast_state("thinking")
        except Exception: pass

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
            if text:
                self._last_interaction_time = time.time()
                logger.info(f"Transcribed: '{text}'")
                # Semantic Confusion Detection
                confusion_keywords = ["what", "repeat", "pardon", "again", "didn't hear", "understand"]
                if any(kw in text.lower() for kw in confusion_keywords):
                    from core.cognition import cognition
                    cognition.trigger("user_confusion", {"text": text})
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
            try:
                from core.jarvis import jarvis
                jarvis._broadcast_state("idle")
            except Exception: pass
        else:
            text = self.transcribe(audio)

        if callback:
            self._invoke_callback(callback, text)

        return text

    def _invoke_callback(self, callback: Callable, text: str):
        """Invoke callback, handling both sync and async functions."""
        if not callback:
            return

        try:
            if inspect.iscoroutinefunction(callback):
                # Schedule on the main event loop
                try:
                    from core.jarvis import jarvis
                    loop = getattr(jarvis, "loop", None)
                    if not loop:
                        try:
                            loop = asyncio.get_running_loop()
                        except RuntimeError:
                            # If we still don't have a loop, we can't schedule the coroutine
                            logger.error("No active event loop found to schedule callback.")
                            return
                except Exception:
                    logger.error("Failed to resolve event loop for callback.")
                    return

                asyncio.run_coroutine_threadsafe(callback(text), loop)
            else:
                callback(text)
        except Exception as e:
            logger.error(f"Callback error: {e}")

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
                        self._invoke_callback(self._callback, text)
            except Exception as e:
                logger.error(f"Continuous listen error: {e}")
                time.sleep(1)

    # ------------------------------------------------------------------
    # Interruption monitoring (Full-Duplex)
    # ------------------------------------------------------------------

    def start_interruption_monitor(self):
        """Start background monitor for user interruptions during TTS."""
        if self._interruption_active:
            return
        self._interruption_active = True
        self._interruption_thread = threading.Thread(
            target=self._interruption_loop,
            daemon=True,
            name="ears-interruption",
        )
        self._interruption_thread.start()
        logger.info("Interruption monitor active.")

    def _interruption_loop(self):
        """Background loop specifically for detecting voice energy spikes during TTS."""
        from senses.mic_bridge import mic_bridge
        from core.jarvis import jarvis
        
        audio_queue = queue.Queue()
        mic_bridge.subscribe(audio_queue.put)
        
        try:
            vocalization_start_time = 0
            while self._interruption_active:
                try:
                    chunk = audio_queue.get(timeout=1.0)
                    chunk_flat = chunk.astype(np.float32) / 32768.0
                    
                    # Only check if JARVIS is actually speaking
                    if jarvis.voice and jarvis.voice.is_speaking:
                        if vocalization_start_time == 0:
                            vocalization_start_time = time.time()
                        
                        # Grace period: Ignore the first 800ms of any vocalization
                        # to avoid initial transients and heavy speaker echo
                        if time.time() - vocalization_start_time < 0.8:
                            continue

                        rms = float(np.sqrt(np.mean(chunk_flat ** 2)))
                        expected = mic_bridge.expected_speaker_rms
                        
                        # Dynamic thresholding
                        # 1. Skip if no baseline (Expected=0 means unknown or silent)
                        if expected <= 1e-4:
                            continue

                        # 2. Feedback ratio (user must be much louder than echo)
                        # 3. Hard noise floor (ignore ambient and feedback noise)
                        if (rms > expected * 25.0) or (rms > 0.9):
                            logger.info(f"User interruption confirmed (RMS: {rms:.4f}, Expected: {expected:.4f})")
                            jarvis.cognition.trigger("voice_interruption", {"rms": rms})
                            jarvis.interrupt()
                            
                            vocalization_start_time = 0
                            time.sleep(1.2)
                    else:
                        vocalization_start_time = 0
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"Interruption check error: {e}")
                    time.sleep(1.0)
        finally:
            mic_bridge.unsubscribe(audio_queue.put)

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

    def get_last_interaction_time(self) -> float:
        """Returns the last timestamp when the user interacted via voice."""
        return self._last_interaction_time

    def check_recent_interaction(self, seconds: int) -> bool:
        """Returns True if the user interacted in the last N seconds."""
        return (time.time() - self._last_interaction_time) < seconds


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
