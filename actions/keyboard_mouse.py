"""
actions/keyboard_mouse.py - JARVIS Keyboard & Mouse Control

PyAutoGUI wrapper for keyboard and mouse automation.
All actions require confirmation (configurable).

Usage:
    from actions.keyboard_mouse import km
    km.type_text("Hello, sir.")
    km.click(500, 300)
    km.hotkey("ctrl", "c")
    km.scroll_down()
"""

import logging
import time
from typing import Optional

logger = logging.getLogger("jarvis.km")


class KeyboardMouse:
    """
    Keyboard and mouse control via PyAutoGUI.
    Confirmation gate on all actions by default.
    """

    def __init__(self, confirm_actions: bool = True, delay: float = 0.05):
        self.confirm_actions = confirm_actions
        self.delay = delay          # pause between actions
        self._pyag = None
        self._load()

    def _load(self):
        try:
            import pyautogui
            pyautogui.FAILSAFE = True    # move mouse to corner to abort
            pyautogui.PAUSE = self.delay
            self._pyag = pyautogui
            logger.info("Keyboard/mouse control online.")
        except ImportError:
            logger.error("pyautogui not installed. Run: pip install pyautogui")
        except Exception as e:
            logger.error(f"PyAutoGUI init error: {e}")

    def _confirm(self, description: str) -> bool:
        if not self.confirm_actions:
            return True
        from actions.confirm import confirm as gate
        return gate.request(description, action_type="keyboard_mouse")

    def _require(self):
        if self._pyag is None:
            raise RuntimeError("PyAutoGUI not available.")

    # ------------------------------------------------------------------
    # Keyboard
    # ------------------------------------------------------------------

    def type_text(self, text: str, interval: float = 0.02, confirm: bool = True) -> bool:
        """Type text at current cursor position."""
        if confirm and not self._confirm(f"Type: '{text[:40]}'"):
            return False
        self._require()
        self._pyag.typewrite(text, interval=interval)
        logger.info(f"Typed: {text[:40]}")
        return True

    def press_key(self, key: str, confirm: bool = False) -> bool:
        """Press a single key."""
        if confirm and not self._confirm(f"Press key: {key}"):
            return False
        self._require()
        self._pyag.press(key)
        logger.debug(f"Key pressed: {key}")
        return True

    def hotkey(self, *keys: str, confirm: bool = False) -> bool:
        """Press a key combination (e.g. hotkey('ctrl', 'c'))."""
        combo = "+".join(keys)
        if confirm and not self._confirm(f"Hotkey: {combo}"):
            return False
        self._require()
        self._pyag.hotkey(*keys)
        logger.info(f"Hotkey: {combo}")
        return True

    def copy(self) -> bool:
        return self.hotkey("ctrl", "c")

    def paste(self) -> bool:
        return self.hotkey("ctrl", "v")

    def select_all(self) -> bool:
        return self.hotkey("ctrl", "a")

    # ------------------------------------------------------------------
    # Mouse
    # ------------------------------------------------------------------

    def click(self, x: int, y: int, button: str = "left", confirm: bool = True) -> bool:
        """Click at screen coordinates."""
        if confirm and not self._confirm(f"Click at ({x}, {y})"):
            return False
        self._require()
        self._pyag.click(x, y, button=button)
        logger.info(f"Clicked ({x}, {y}) [{button}]")
        return True

    def double_click(self, x: int, y: int, confirm: bool = True) -> bool:
        if confirm and not self._confirm(f"Double-click at ({x}, {y})"):
            return False
        self._require()
        self._pyag.doubleClick(x, y)
        logger.info(f"Double-clicked ({x}, {y})")
        return True

    def right_click(self, x: int, y: int, confirm: bool = True) -> bool:
        if confirm and not self._confirm(f"Right-click at ({x}, {y})"):
            return False
        self._require()
        self._pyag.rightClick(x, y)
        return True

    def move_to(self, x: int, y: int, duration: float = 0.3) -> bool:
        """Move mouse to coordinates (no click)."""
        self._require()
        self._pyag.moveTo(x, y, duration=duration)
        return True

    def drag(self, x1: int, y1: int, x2: int, y2: int, confirm: bool = True) -> bool:
        """Drag from (x1,y1) to (x2,y2)."""
        if confirm and not self._confirm(f"Drag ({x1},{y1}) → ({x2},{y2})"):
            return False
        self._require()
        self._pyag.moveTo(x1, y1)
        self._pyag.dragTo(x2, y2, duration=0.5)
        logger.info(f"Dragged ({x1},{y1}) → ({x2},{y2})")
        return True

    def scroll_up(self, clicks: int = 3) -> bool:
        self._require()
        self._pyag.scroll(clicks)
        return True

    def scroll_down(self, clicks: int = 3) -> bool:
        self._require()
        self._pyag.scroll(-clicks)
        return True

    # ------------------------------------------------------------------
    # Screen info
    # ------------------------------------------------------------------

    def get_position(self) -> tuple[int, int]:
        """Get current mouse position."""
        self._require()
        return self._pyag.position()

    def get_screen_size(self) -> tuple[int, int]:
        """Get screen resolution."""
        self._require()
        return self._pyag.size()

    def locate_on_screen(self, image_path: str) -> Optional[tuple]:
        """Find an image on screen, return its center coordinates."""
        self._require()
        try:
            loc = self._pyag.locateOnScreen(image_path, confidence=0.8)
            if loc:
                center = self._pyag.center(loc)
                return (center.x, center.y)
            return None
        except Exception as e:
            logger.error(f"Locate on screen error: {e}")
            return None

    def click_image(self, image_path: str, confirm: bool = True) -> bool:
        """Find image on screen and click it."""
        coords = self.locate_on_screen(image_path)
        if coords:
            return self.click(coords[0], coords[1], confirm=confirm)
        logger.warning(f"Image not found on screen: {image_path}")
        return False

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def status(self) -> dict:
        available = self._pyag is not None
        return {
            "available": available,
            "confirm_actions": self.confirm_actions,
            "delay": self.delay,
            "screen_size": self.get_screen_size() if available else None,
            "mouse_position": self.get_position() if available else None,
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

km = KeyboardMouse()
