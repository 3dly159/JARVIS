"""
senses/mic_bridge.py - JARVIS Unified Mic Bridge

Manages a single sounddevice.InputStream to prevent resource contention.
Distributes audio chunks to multiple subscribers (Wake word, STT, etc).
"""

import logging
import threading
import queue
import numpy as np
from typing import Callable, List

logger = logging.getLogger("jarvis.mic_bridge")

SAMPLE_RATE = 16000
CHUNK_DURATION = 0.08  # 80ms
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_DURATION)

class MicBridge:
    """
    Singleton bridge that holds the microphone open and 
    multicasts audio chunks to all subscribers.
    """
    def __init__(self):
        self.subscribers: List[Callable[[np.ndarray], None]] = []
        self._lock = threading.Lock()
        self._running = False
        self._stream = None
        self._thread = None
        self.expected_speaker_rms = 0.0  # Shared baseline for vocal suppression

    def subscribe(self, callback: Callable[[np.ndarray], None]):
        """Add a callback to receive every audio chunk."""
        with self._lock:
            if callback not in self.subscribers:
                self.subscribers.append(callback)
                logger.debug("New subscriber added.")
            
            # Auto-start if it's the first subscriber
            if not self._running:
                self.start()

    def unsubscribe(self, callback: Callable[[np.ndarray], None]):
        """Remove a callback."""
        with self._lock:
            if callback in self.subscribers:
                self.subscribers.remove(callback)
                logger.debug("Subscriber removed.")
            
            # Auto-stop if no more subscribers
            if not self.subscribers:
                self.stop()

    def start(self):
        """Start the master microphone stream."""
        if self._running:
            return
        
        try:
            import sounddevice as sd
            self._running = True
            logger.info("Opening master microphone stream...")
            
            self._stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="int16",
                blocksize=CHUNK_SAMPLES,
                callback=self._audio_callback
            )
            self._stream.start()
            logger.info("Master microphone stream active.")
        except Exception as e:
            logger.error(f"Failed to start master mic stream: {e}")
            self._running = False

    def stop(self):
        """Stop the master microphone stream."""
        self._running = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        logger.info("Master microphone stream closed.")

    def _audio_callback(self, indata, frames, time, status):
        """Callback from sounddevice - multicasts to all subscribers."""
        if status:
            logger.warning(f"Mic status error: {status}")
            
        # Copy audio to avoid buffer reuse issues
        chunk = indata.flatten().copy()
        
        # Dispatch to all subscribers via a background thread to avoid blocking the Pa stream
        def dispatch():
            with self._lock:
                for callback in self.subscribers:
                    try:
                        callback(chunk)
                    except Exception as e:
                        logger.error(f"Subscriber callback error: {e}")
        
        threading.Thread(target=dispatch, daemon=True).start()

# Singleton instance
mic_bridge = MicBridge()
