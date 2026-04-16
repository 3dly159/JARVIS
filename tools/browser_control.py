"""
tools/browser_control.py - JARVIS Browser Control

Playwright-based browser automation.
Open URLs, click, type, extract text, take screenshots.
Auto-registers with tool registry on import.

Usage:
    from tools.browser_control import browser
    text = browser.get_text("https://example.com")
    browser.open("https://google.com")
"""

import logging
from typing import Optional

logger = logging.getLogger("jarvis.tools.browser")


class BrowserControl:
    """Playwright browser automation."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright = None
        self._browser = None
        self._page = None

    def _ensure_started(self):
        """Lazy-start Playwright."""
        if self._page is not None:
            return
        try:
            from playwright.sync_api import sync_playwright
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=self.headless)
            self._page = self._browser.new_page()
            logger.info("Browser started.")
        except ImportError:
            raise RuntimeError("playwright not installed. Run: pip install playwright && playwright install chromium")
        except Exception as e:
            raise RuntimeError(f"Browser start failed: {e}")

    def open(self, url: str, wait_ms: int = 2000) -> bool:
        """Navigate to a URL."""
        try:
            self._ensure_started()
            self._page.goto(url, timeout=30000)
            self._page.wait_for_timeout(wait_ms)
            logger.info(f"Opened: {url}")
            return True
        except Exception as e:
            logger.error(f"Browser open error: {e}")
            return False

    def get_text(self, url: str) -> str:
        """Fetch a page and return its visible text content."""
        try:
            self._ensure_started()
            self._page.goto(url, timeout=30000)
            self._page.wait_for_load_state("domcontentloaded")
            text = self._page.inner_text("body")
            # Trim whitespace and limit length
            text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
            if len(text) > 5000:
                text = text[:5000] + "\n\n[...truncated]"
            logger.info(f"Got text from: {url} ({len(text)} chars)")
            return text
        except Exception as e:
            logger.error(f"Get text error: {e}")
            return f"Error fetching {url}: {e}"

    def click(self, selector: str) -> bool:
        """Click an element by CSS selector."""
        try:
            self._ensure_started()
            self._page.click(selector, timeout=5000)
            return True
        except Exception as e:
            logger.error(f"Click error ({selector}): {e}")
            return False

    def type_text(self, selector: str, text: str) -> bool:
        """Type text into an input field."""
        try:
            self._ensure_started()
            self._page.fill(selector, text)
            return True
        except Exception as e:
            logger.error(f"Type error ({selector}): {e}")
            return False

    def screenshot(self, path: str = "/tmp/browser_screenshot.png") -> bool:
        """Take a screenshot of the current page."""
        try:
            self._ensure_started()
            self._page.screenshot(path=path)
            logger.info(f"Browser screenshot saved: {path}")
            return True
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return False

    def get_title(self) -> str:
        try:
            self._ensure_started()
            return self._page.title()
        except Exception:
            return ""

    def get_url(self) -> str:
        try:
            self._ensure_started()
            return self._page.url
        except Exception:
            return ""

    def close(self):
        """Close the browser."""
        try:
            if self._browser:
                self._browser.close()
            if self._playwright:
                self._playwright.stop()
            self._page = None
            self._browser = None
            self._playwright = None
            logger.info("Browser closed.")
        except Exception as e:
            logger.error(f"Browser close error: {e}")

    def status(self) -> dict:
        return {
            "started": self._page is not None,
            "headless": self.headless,
            "current_url": self.get_url() if self._page else None,
        }


# ---------------------------------------------------------------------------
# Singleton + auto-register
# ---------------------------------------------------------------------------

browser = BrowserControl(headless=True)

from tools.registry import registry
registry.register(
    name="browse_url",
    description="Open a URL in a browser and extract its text content. Use for reading web pages.",
    handler=lambda url, **_: browser.get_text(url),
    params={"url": "full URL to browse (https://...)"},
)
