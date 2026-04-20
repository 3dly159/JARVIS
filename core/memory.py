"""
core/memory.py - JARVIS Memory System
Daily log files + Memory Palace (long-term important items).
"""

import json
import logging
import os
import re
from datetime import datetime, date
from pathlib import Path
from typing import Optional

logger = logging.getLogger("jarvis.memory")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

MEMORY_DIR = Path(__file__).parent.parent / "memory"
PALACE_DIR = MEMORY_DIR / "palace"


def _ensure_dirs():
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    PALACE_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Daily Log
# ---------------------------------------------------------------------------

class DailyLog:
    """
    One markdown file per day: memory/YYYY-MM-DD.md
    Append-only raw log of everything that happens.
    """

    def __init__(self, log_date: Optional[date] = None):
        _ensure_dirs()
        self.log_date = log_date or date.today()
        self.path = MEMORY_DIR / f"{self.log_date.isoformat()}.md"
        self._ensure_file()

    def _ensure_file(self):
        if not self.path.exists():
            self.path.write_text(
                f"# JARVIS Daily Log — {self.log_date.strftime('%A, %d %B %Y')}\n\n"
            )
            logger.info(f"Created daily log: {self.path.name}")

    def append(self, entry: str, category: str = "note"):
        """Append a timestamped entry to today's log."""
        timestamp = datetime.now().strftime("%H:%M")
        line = f"\n## [{timestamp}] {category.upper()}\n{entry.strip()}\n"
        with self.path.open("a", encoding="utf-8") as f:
            f.write(line)
        logger.debug(f"Daily log entry [{category}]: {entry[:60]}...")

    def read(self) -> str:
        """Read the full day's log."""
        return self.path.read_text(encoding="utf-8") if self.path.exists() else ""

    def read_date(self, log_date: date) -> str:
        """Read log for a specific date."""
        path = MEMORY_DIR / f"{log_date.isoformat()}.md"
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def list_dates(self) -> list[str]:
        """List all available daily log dates."""
        return sorted([
            p.stem for p in MEMORY_DIR.glob("????-??-??.md")
        ], reverse=True)


# ---------------------------------------------------------------------------
# Memory Palace
# ---------------------------------------------------------------------------

class MemoryPalace:
    """
    Long-term important memory items.
    Each item is a JSON file in memory/palace/
    Tagged, searchable, and retrievable by JARVIS at any time.
    """

    def __init__(self):
        _ensure_dirs()

    def _item_path(self, item_id: str) -> Path:
        return PALACE_DIR / f"{item_id}.json"

    def store(
        self,
        content: str,
        tags: list[str] = None,
        title: str = "",
        item_id: Optional[str] = None,
    ) -> str:
        """
        Store an important item in the Memory Palace.
        Returns the item_id.
        """
        if not item_id:
            # Generate ID from timestamp
            item_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        item = {
            "id": item_id,
            "title": title or content[:60],
            "content": content,
            "tags": tags or [],
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
        }

        self._item_path(item_id).write_text(
            json.dumps(item, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info(f"Memory Palace: stored '{item['title']}' [{item_id}]")
        return item_id

    def recall(self, item_id: str) -> Optional[dict]:
        """Retrieve a specific item by ID."""
        path = self._item_path(item_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def update(self, item_id: str, content: str = None, tags: list[str] = None):
        """Update an existing Palace item."""
        item = self.recall(item_id)
        if not item:
            logger.warning(f"Memory Palace: item '{item_id}' not found for update")
            return
        if content:
            item["content"] = content
        if tags is not None:
            item["tags"] = tags
        item["updated"] = datetime.now().isoformat()
        self._item_path(item_id).write_text(
            json.dumps(item, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info(f"Memory Palace: updated '{item_id}'")

    def forget(self, item_id: str):
        """Remove an item from the Palace."""
        path = self._item_path(item_id)
        if path.exists():
            path.unlink()
            logger.info(f"Memory Palace: removed '{item_id}'")

    def search(self, query: str, tags: list[str] = None) -> list[dict]:
        """
        Search Palace items by keyword and/or tags.
        Returns matching items sorted by relevance (simple keyword match).
        """
        query_lower = query.lower()
        results = []

        for path in PALACE_DIR.glob("*.json"):
            try:
                item = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue

            # Tag filter
            if tags and not any(t in item.get("tags", []) for t in tags):
                continue

            # Keyword match in title + content + tags
            searchable = (
                item.get("title", "") + " " +
                item.get("content", "") + " " +
                " ".join(item.get("tags", []))
            ).lower()

            if query_lower in searchable:
                # Simple relevance: count occurrences
                score = searchable.count(query_lower)
                results.append((score, item))

        results.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in results]

    def list_all(self) -> list[dict]:
        """List all Palace items (title + id + tags only)."""
        items = []
        for path in sorted(PALACE_DIR.glob("*.json")):
            try:
                item = json.loads(path.read_text(encoding="utf-8"))
                items.append({
                    "id": item["id"],
                    "title": item["title"],
                    "content": item.get("content", ""),
                    "tags": item.get("tags", []),
                    "created": item.get("created", ""),
                    "updated": item.get("updated", ""),
                })
            except Exception:
                continue
        return items

    def summary(self) -> str:
        """Returns a short text summary of Palace contents for context injection."""
        items = self.list_all()
        if not items:
            return "Memory Palace is empty."
        lines = ["Memory Palace contents:"]
        for item in items:
            tags = f" [{', '.join(item['tags'])}]" if item["tags"] else ""
            lines.append(f"  - [{item['id']}] {item['title']}{tags}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Memory Manager (unified interface)
# ---------------------------------------------------------------------------

class Memory:
    """
    Unified memory interface for JARVIS.
    All modules use this instead of DailyLog/MemoryPalace directly.
    """

    def __init__(self):
        self.daily = DailyLog()
        self.palace = MemoryPalace()
        logger.info("Memory system online.")

    # ----- Daily log shortcuts -----

    def log(self, entry: str, category: str = "note"):
        """Append to today's daily log."""
        self.daily.append(entry, category)

    def log_conversation(self, role: str, content: str):
        """Log a conversation turn."""
        self.daily.append(f"**{role.upper()}:** {content}", "conversation")

    def log_action(self, action: str, result: str = ""):
        """Log an action taken by JARVIS."""
        entry = action + (f"\nResult: {result}" if result else "")
        self.daily.append(entry, "action")

    def log_error(self, error: str):
        """Log an error."""
        self.daily.append(error, "error")

    def today(self) -> str:
        """Read today's full log."""
        return self.daily.read()

    # ----- Palace shortcuts -----

    def remember(self, content: str, title: str = "", tags: list[str] = None) -> str:
        """Store something important in the Memory Palace. Returns item_id."""
        return self.palace.store(content, tags=tags, title=title)

    def recall(self, query: str) -> list[dict]:
        """Search the Memory Palace."""
        return self.palace.search(query)

    def forget(self, item_id: str):
        """Remove from Memory Palace."""
        self.palace.forget(item_id)

    # ----- Context for brain -----

    def get_context_summary(self) -> str:
        """
        Returns a compact memory summary to inject into the brain's context.
        Called at session start and periodically.
        """
        today_log = self.daily.read()
        palace_summary = self.palace.summary()

        # Truncate today's log if very long
        if len(today_log) > 2000:
            today_log = today_log[-2000:]
            today_log = "[...truncated...]\n" + today_log

        return (
            f"=== TODAY'S LOG ===\n{today_log}\n\n"
            f"=== {palace_summary} ==="
        )

    def status(self) -> dict:
        return {
            "daily_logs": self.daily.list_dates(),
            "palace_items": len(self.palace.list_all()),
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

memory = Memory()


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Testing JARVIS memory...\n")

    memory.log("System initialized.", "system")
    memory.log_conversation("user", "Hello JARVIS.")
    memory.log_conversation("jarvis", "Good evening, sir.")

    item_id = memory.remember(
        "User's name is Mohab. Prefers MCU-style JARVIS personality.",
        title="User profile",
        tags=["user", "preferences"],
    )
    print(f"Stored in Palace: {item_id}")

    results = memory.recall("Mohab")
    print(f"Recalled: {results[0]['title'] if results else 'nothing'}")

    print("\nContext summary preview:")
    print(memory.get_context_summary()[:500])
    print("\nStatus:", memory.status())
