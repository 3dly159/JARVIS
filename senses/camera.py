"""
senses/camera.py - JARVIS Camera (On-Demand)

OpenCV camera capture. JARVIS opens the camera only when needed.
Single frame or short clip. Self-aware: JARVIS knows it has a camera.

Usage:
    from senses.camera import camera
    frame = camera.snap()              # single frame → base64 JPEG
    clip = camera.record(seconds=3)    # short clip → list of base64 frames
    camera.save_snap("/tmp/face.jpg")  # save to disk
"""

import base64
import io
import logging
import threading
import time
from typing import Optional

logger = logging.getLogger("jarvis.camera")


class Camera:
    """
    On-demand camera capture via OpenCV.
    Camera is opened only when actively used, then released.
    """

    def __init__(
        self,
        device_index: int = 0,
        resolution: tuple = (640, 480),
        fps: int = 30,
        jpeg_quality: int = 85,
    ):
        self.device_index = device_index
        self.resolution = resolution
        self.fps = fps
        self.jpeg_quality = jpeg_quality
        self.enabled = True
        self._lock = threading.Lock()
        self._available: Optional[bool] = None  # cached availability check

        logger.info(f"Camera module ready. Device: {device_index}, Resolution: {resolution}")

    # ------------------------------------------------------------------
    # Availability check
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        """Check if camera hardware is accessible."""
        if self._available is not None:
            return self._available
        try:
            import cv2
            cap = cv2.VideoCapture(self.device_index)
            available = cap.isOpened()
            cap.release()
            self._available = available
            if available:
                logger.info(f"Camera available at device {self.device_index}.")
            else:
                logger.warning(f"Camera device {self.device_index} not available.")
            return available
        except ImportError:
            logger.error("opencv-python not installed. Run: pip install opencv-python")
            return False
        except Exception as e:
            logger.error(f"Camera check error: {e}")
            return False

    # ------------------------------------------------------------------
    # Single frame
    # ------------------------------------------------------------------

    def snap(self, encode: bool = True) -> Optional[str]:
        """
        Capture a single frame.
        encode=True  → returns base64 JPEG string
        encode=False → returns raw JPEG bytes
        Returns None if camera unavailable.
        """
        if not self.enabled:
            logger.debug("Camera disabled.")
            return None

        with self._lock:
            try:
                from core.jarvis import jarvis
                jarvis._broadcast_state("seeing")
            except Exception: pass

            try:
                import cv2

                cap = cv2.VideoCapture(self.device_index)
                if not cap.isOpened():
                    logger.warning("Cannot open camera.")
                    return None

                # Set resolution
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])

                # Warm up (discard first few frames — some cameras need this)
                for _ in range(3):
                    cap.read()

                ret, frame = cap.read()
                cap.release()

                if not ret or frame is None:
                    logger.warning("Failed to capture frame.")
                    return None

                # Encode to JPEG
                encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality]
                _, jpeg_buf = cv2.imencode(".jpg", frame, encode_params)
                jpeg_bytes = jpeg_buf.tobytes()

                logger.debug("Camera snap captured.")

                if encode:
                    return base64.b64encode(jpeg_bytes).decode("utf-8")
                return jpeg_bytes

            except ImportError:
                logger.error("opencv-python not installed.")
                return None
            except Exception as e:
                logger.error(f"Camera snap error: {e}")
                return None

    def save_snap(self, path: str) -> bool:
        """Capture and save a frame to disk."""
        raw = self.snap(encode=False)
        if raw is None:
            return False
        try:
            with open(path, "wb") as f:
                f.write(raw)
            logger.info(f"Camera snap saved: {path}")
            return True
        except Exception as e:
            logger.error(f"Save snap error: {e}")
            return False

    # ------------------------------------------------------------------
    # Short clip
    # ------------------------------------------------------------------

    def record(self, seconds: float = 3.0) -> list[str]:
        """
        Capture a short clip. Returns list of base64 JPEG frames.
        Uses fps setting to determine frame count.
        """
        if not self.enabled:
            return []

        frames = []
        frame_count = int(seconds * self.fps)
        interval = 1.0 / self.fps

        with self._lock:
            try:
                from core.jarvis import jarvis
                jarvis._broadcast_state("seeing")
            except Exception: pass

            try:
                import cv2

                cap = cv2.VideoCapture(self.device_index)
                if not cap.isOpened():
                    logger.warning("Cannot open camera for recording.")
                    return []

                cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
                cap.set(cv2.CAP_PROP_FPS, self.fps)

                logger.info(f"Recording {seconds}s clip ({frame_count} frames)...")
                encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality]

                for _ in range(frame_count):
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        _, jpeg_buf = cv2.imencode(".jpg", frame, encode_params)
                        frames.append(base64.b64encode(jpeg_buf.tobytes()).decode("utf-8"))
                    time.sleep(interval)

                cap.release()
                logger.info(f"Clip captured: {len(frames)} frames.")

            except Exception as e:
                logger.error(f"Camera record error: {e}")

        return frames

    def save_clip(self, path: str, seconds: float = 3.0) -> bool:
        """Record a clip and save as MP4."""
        with self._lock:
            try:
                import cv2

                cap = cv2.VideoCapture(self.device_index)
                if not cap.isOpened():
                    return False

                cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])

                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                out = cv2.VideoWriter(path, fourcc, self.fps, self.resolution)

                end_time = time.time() + seconds
                while time.time() < end_time:
                    ret, frame = cap.read()
                    if ret:
                        out.write(frame)

                cap.release()
                out.release()
                logger.info(f"Clip saved: {path}")
                return True

            except Exception as e:
                logger.error(f"Save clip error: {e}")
                return False

    # ------------------------------------------------------------------
    # List available cameras
    # ------------------------------------------------------------------

    @staticmethod
    def list_devices() -> list[int]:
        """Return list of available camera device indices."""
        try:
            import cv2
            available = []
            for i in range(5):
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    available.append(i)
                    cap.release()
            return available
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Presence detection
    # ------------------------------------------------------------------

    def is_user_present(self) -> bool:
        """
        Check if a face is visible in front of the camera.
        Lightweight check via Haar cascades.
        """
        if not self.enabled or not self.is_available():
            return True # Fallback if camera unavailable
            
        try:
            import cv2
            import numpy as np
            import os

            # Snap a frame (internal lock handled by snap())
            raw_jpeg = self.snap(encode=False)
            if not raw_jpeg:
                return False

            # Load face cascade
            cascade_path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
            if not os.path.exists(cascade_path):
                logger.warning(f"Haar cascade file not found at {cascade_path}")
                return True

            face_cascade = cv2.CascadeClassifier(cascade_path)

            # Decode bytes to image
            nparr = np.frombuffer(raw_jpeg, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                return False

            # Convert to gray
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Detect faces
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            present = len(faces) > 0
            
            if present:
                logger.info(f"User presence confirmed ({len(faces)} face(s)).")
            else:
                logger.debug("No user detected in camera view.")
                
            return present

        except Exception as e:
            logger.error(f"Presence detection failed: {e}")
            return True # Conservative fallback

    # ------------------------------------------------------------------
    # Context for brain
    # ------------------------------------------------------------------

    def get_context_frame(self) -> Optional[str]:
        """Get a camera frame as base64 for injecting into brain context."""
        return self.snap(encode=True)

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def status(self) -> dict:
        return {
            "device_index": self.device_index,
            "resolution": self.resolution,
            "fps": self.fps,
            "enabled": self.enabled,
            "available": self.is_available(),
            "available_devices": self.list_devices(),
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

camera = Camera()


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Testing JARVIS camera...\n")

    print("Available devices:", Camera.list_devices())

    if camera.is_available():
        print("Capturing frame...")
        frame = camera.snap()
        if frame:
            print(f"Frame captured. Base64 length: {len(frame)} chars")
            import base64
            with open("/tmp/jarvis_camera_test.jpg", "wb") as f:
                f.write(base64.b64decode(frame))
            print("Saved to /tmp/jarvis_camera_test.jpg")

        print("\nRecording 2s clip...")
        frames = camera.record(seconds=2.0)
        print(f"Captured {len(frames)} frames.")
    else:
        print("No camera available.")

    print("\nStatus:", camera.status())
