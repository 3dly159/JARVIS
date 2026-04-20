"""
senses/eyes.py - JARVIS Eyes (Screen Capture)

Live screen capture via mss.
Smart triggers: captures on significant change, not constant polling.
Feeds frames to brain as context when relevant.

Usage:
    from senses.eyes import eyes
    frame = eyes.capture()             # single screenshot → base64
    eyes.start_watching(callback)      # background change detection
    eyes.stop_watching()
"""

import base64
import hashlib
import io
import logging
import threading
import time
from typing import Callable, Optional

logger = logging.getLogger("jarvis.eyes")

# Defaults
DEFAULT_MONITOR = 1          # Primary monitor
CHANGE_THRESHOLD = 0.02      # 2% pixel change = significant
WATCH_INTERVAL = 1.0         # seconds between checks
CAPTURE_SCALE = 0.5          # scale down for faster processing (0.5 = half size)
JPEG_QUALITY = 70            # JPEG quality for encoded frames


class Eyes:
    """
    Screen capture with smart change detection.
    Only triggers callback when the screen changes meaningfully.
    """

    def __init__(
        self,
        monitor: int = DEFAULT_MONITOR,
        change_threshold: float = CHANGE_THRESHOLD,
        watch_interval: float = WATCH_INTERVAL,
        scale: float = CAPTURE_SCALE,
    ):
        self.monitor = monitor
        self.change_threshold = change_threshold
        self.watch_interval = watch_interval
        self.scale = scale
        self.enabled = True

        self._watching = False
        self._watch_thread: Optional[threading.Thread] = None
        self._callback: Optional[Callable] = None
        self._last_hash: Optional[str] = None
        self._last_frame: Optional[bytes] = None   # JPEG bytes

        logger.info(f"Eyes online. Monitor: {monitor}, change threshold: {change_threshold:.0%}")

    # ------------------------------------------------------------------
    # Single capture
    # ------------------------------------------------------------------

    def capture(self, encode: bool = True) -> Optional[str]:
        """
        Capture current screen.
        encode=True  → returns base64 JPEG string (for LLM context)
        encode=False → returns raw JPEG bytes
        """
        try:
            from core.jarvis import jarvis
            jarvis._broadcast_state("seeing")
        except Exception: pass

        try:
            import mss
            import mss.tools
            from PIL import Image

            with mss.mss() as sct:
                monitors = sct.monitors
                if self.monitor >= len(monitors):
                    mon = monitors[1]  # fallback to primary
                else:
                    mon = monitors[self.monitor]

                screenshot = sct.grab(mon)
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

                # Scale down
                if self.scale != 1.0:
                    new_w = int(img.width * self.scale)
                    new_h = int(img.height * self.scale)
                    img = img.resize((new_w, new_h), Image.LANCZOS)

                # Encode to JPEG
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=JPEG_QUALITY)
                jpeg_bytes = buf.getvalue()
                self._last_frame = jpeg_bytes

                if encode:
                    return base64.b64encode(jpeg_bytes).decode("utf-8")
                return jpeg_bytes

        except ImportError as e:
            logger.error(f"Missing dependency: {e}. Install: pip install mss Pillow")
            return None
        except Exception as e:
            logger.error(f"Screen capture error: {e}")
            return None

    def capture_region(self, x: int, y: int, width: int, height: int) -> Optional[str]:
        """Capture a specific region of the screen. Returns base64 JPEG."""
        try:
            import mss
            from PIL import Image

            with mss.mss() as sct:
                region = {"top": y, "left": x, "width": width, "height": height}
                screenshot = sct.grab(region)
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=JPEG_QUALITY)
                return base64.b64encode(buf.getvalue()).decode("utf-8")

        except Exception as e:
            logger.error(f"Region capture error: {e}")
            return None

    def save_screenshot(self, path: str) -> bool:
        """Save current screenshot to file."""
        try:
            import mss
            from PIL import Image

            with mss.mss() as sct:
                monitors = sct.monitors
                mon = monitors[min(self.monitor, len(monitors) - 1)]
                screenshot = sct.grab(mon)
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                img.save(path)
                logger.info(f"Screenshot saved: {path}")
                return True
        except Exception as e:
            logger.error(f"Save screenshot error: {e}")
            return False

    # ------------------------------------------------------------------
    # Change detection
    # ------------------------------------------------------------------

    def _frame_hash(self, jpeg_bytes: bytes) -> str:
        """Fast perceptual hash for change detection."""
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(jpeg_bytes))
            # Tiny thumbnail for fast comparison
            thumb = img.resize((16, 16), Image.LANCZOS).convert("L")
            return hashlib.md5(thumb.tobytes()).hexdigest()
        except Exception:
            return hashlib.md5(jpeg_bytes[:1000]).hexdigest()

    def _change_ratio(self, hash1: str, hash2: str) -> float:
        """Estimate change ratio from two hashes. Simple binary: changed or not."""
        return 0.0 if hash1 == hash2 else 1.0

    def has_changed(self) -> bool:
        """Returns True if screen has changed since last check."""
        frame = self.capture(encode=False)
        if frame is None:
            return False
        current_hash = self._frame_hash(frame)
        changed = self._last_hash is None or current_hash != self._last_hash
        self._last_hash = current_hash
        return changed

    # ------------------------------------------------------------------
    # Continuous watching
    # ------------------------------------------------------------------

    def start_watching(self, callback: Callable[[str], None]):
        """
        Watch screen for changes in background.
        Calls callback(base64_jpeg) when significant change detected.
        """
        if self._watching:
            logger.warning("Already watching screen.")
            return

        self._watching = True
        self._callback = callback
        self._watch_thread = threading.Thread(
            target=self._watch_loop,
            daemon=True,
            name="eyes-watch",
        )
        self._watch_thread.start()
        logger.info("Screen watching started.")

    def stop_watching(self):
        self._watching = False
        logger.info("Screen watching stopped.")

    def _watch_loop(self):
        while self._watching:
            try:
                if self.enabled and self.has_changed():
                    frame_b64 = self.capture(encode=True)
                    if frame_b64 and self._callback:
                        self._callback(frame_b64)
                time.sleep(self.watch_interval)
            except Exception as e:
                logger.error(f"Watch loop error: {e}")
                time.sleep(2)

    # ------------------------------------------------------------------
    # Context for brain
    # ------------------------------------------------------------------

    def get_context_frame(self) -> Optional[str]:
        """Get current screen as base64 for injecting into brain context."""
        return self.capture(encode=True)

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def status(self) -> dict:
        return {
            "monitor": self.monitor,
            "enabled": self.enabled,
            "watching": self._watching,
            "change_threshold": self.change_threshold,
            "watch_interval": self.watch_interval,
            "scale": self.scale,
            "has_last_frame": self._last_frame is not None,
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

eyes = Eyes()


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Testing JARVIS eyes (screen capture)...\n")

    frame = eyes.capture()
    if frame:
        print(f"Screenshot captured. Base64 length: {len(frame)} chars")
        # Save to file for visual check
        import base64
        with open("/tmp/jarvis_screen_test.jpg", "wb") as f:
            f.write(base64.b64decode(frame))
        print("Saved to /tmp/jarvis_screen_test.jpg")
    else:
        print("Capture failed — check mss + Pillow installation.")

    print("\nWatching for screen changes (5 seconds)...")
    changes = []
    eyes.start_watching(lambda f: changes.append(len(f)))
    time.sleep(5)
    eyes.stop_watching()
    print(f"Detected {len(changes)} change(s).")
    print("\nStatus:", eyes.status())
