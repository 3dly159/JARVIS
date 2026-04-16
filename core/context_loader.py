"""
core/context_loader.py - JARVIS Context Loader

Reads AGENTS.md and all registered instruction files at session start.
Assembles a dynamic system prompt from: IDENTITY.md, SOUL.md, USER.md,
today's memory log, and Memory Palace summary.

brain.py uses this instead of a hardcoded system prompt.
"""

import logging
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger("jarvis.context_loader")

# ---------------------------------------------------------------------------
# Root directory (JARVIS/)
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# File Reader
# ---------------------------------------------------------------------------

def _read(path: Path, label: str = "") -> str:
    """Read a file, return empty string with warning if missing."""
    if path.exists():
        content = path.read_text(encoding="utf-8").strip()
        logger.debug(f"Loaded: {path.name}")
        return content
    else:
        logger.warning(f"Missing context file: {path} [{label}]")
        return f"[{label or path.name} not found]"


# ---------------------------------------------------------------------------
# Memory Palace Summary
# ---------------------------------------------------------------------------

def _palace_summary(palace_dir: Path) -> str:
    """Build a short summary of Memory Palace items."""
    if not palace_dir.exists():
        return "Memory Palace: empty."

    import json
    items = []
    for f in sorted(palace_dir.glob("*.json")):
        try:
            item = json.loads(f.read_text(encoding="utf-8"))
            tags = f"[{', '.join(item.get('tags', []))}]" if item.get("tags") else ""
            items.append(f"  - [{item['id']}] {item['title']} {tags}".strip())
        except Exception:
            continue

    if not items:
        return "Memory Palace: empty."
    return "Memory Palace:\n" + "\n".join(items)


# ---------------------------------------------------------------------------
# Daily Memory Loader
# ---------------------------------------------------------------------------

def _load_daily_memory(memory_dir: Path, max_chars: int = 3000) -> str:
    """
    Load today's daily log. If sparse (<200 chars), also load yesterday's.
    Truncates to max_chars to avoid blowing the context window.
    """
    today = date.today()
    yesterday = today - timedelta(days=1)

    today_path = memory_dir / f"{today.isoformat()}.md"
    yesterday_path = memory_dir / f"{yesterday.isoformat()}.md"

    today_content = today_path.read_text(encoding="utf-8").strip() if today_path.exists() else ""
    yesterday_content = ""

    # If today is sparse, pull yesterday too
    if len(today_content) < 200 and yesterday_path.exists():
        yesterday_content = yesterday_path.read_text(encoding="utf-8").strip()

    combined = ""
    if yesterday_content:
        combined += f"=== Yesterday ({yesterday.isoformat()}) ===\n{yesterday_content}\n\n"
    combined += f"=== Today ({today.isoformat()}) ===\n{today_content}" if today_content else f"=== Today ({today.isoformat()}) ===\n(no entries yet)"

    # Truncate from the front if too long (keep the most recent)
    if len(combined) > max_chars:
        combined = "[...older entries truncated...]\n" + combined[-max_chars:]

    return combined


# ---------------------------------------------------------------------------
# Extra Files Parser (from AGENTS.md table)
# ---------------------------------------------------------------------------

def _parse_extra_files(agents_md: str) -> list[Path]:
    """
    Parse AGENTS.md for any extra registered files beyond the core set.
    Looks for markdown table rows pointing to .md files.
    Returns list of Paths for files not already in the core load order.
    """
    core_files = {"IDENTITY.md", "SOUL.md", "USER.md", "AGENTS.md"}
    extra = []

    # Match table rows like: | `some/file.md` | Description |
    pattern = re.compile(r"\|\s*`([^`]+\.md)`\s*\|")
    for match in pattern.finditer(agents_md):
        filename = match.group(1)
        if filename not in core_files and "YYYY" not in filename:
            path = ROOT / filename
            if path.exists():
                extra.append(path)

    return extra


# ---------------------------------------------------------------------------
# Main Loader
# ---------------------------------------------------------------------------

class ContextLoader:
    """
    Assembles JARVIS's full system prompt from instruction files.
    Call load() at session start, and refresh() periodically.
    """

    def __init__(self, root: Path = ROOT):
        self.root = root
        self.memory_dir = root / "memory"
        self.palace_dir = root / "memory" / "palace"
        self._cached_prompt: Optional[str] = None

    def load(self, force: bool = False) -> str:
        """
        Load and assemble the full system prompt.
        Cached after first load; use force=True to reload from disk.
        """
        if self._cached_prompt and not force:
            return self._cached_prompt

        from datetime import datetime
        now = datetime.now().strftime("%A, %d %B %Y %H:%M")

        sections = []

        # 1. Header
        sections.append(f"# JARVIS — Session Context\nLoaded: {now}\n")

        # 2. AGENTS.md (navigation, not injected verbatim — just parse extras)
        agents_path = self.root / "AGENTS.md"
        agents_content = _read(agents_path, "AGENTS.md")

        # 3. IDENTITY.md
        identity = _read(self.root / "IDENTITY.md", "IDENTITY.md")
        sections.append(f"## IDENTITY\n{identity}")

        # 4. SOUL.md
        soul = _read(self.root / "SOUL.md", "SOUL.md")
        sections.append(f"## SOUL\n{soul}")

        # 5. USER.md
        user = _read(self.root / "USER.md", "USER.md")
        sections.append(f"## USER\n{user}")

        # 6. Any extra registered files from AGENTS.md
        extra_files = _parse_extra_files(agents_content)
        for path in extra_files:
            content = _read(path, path.name)
            sections.append(f"## {path.stem.upper()}\n{content}")
            logger.info(f"Loaded extra context file: {path.name}")

        # 7. Daily memory
        daily = _load_daily_memory(self.memory_dir)
        sections.append(f"## MEMORY — DAILY LOG\n{daily}")

        # 8. Memory Palace
        palace = _palace_summary(self.palace_dir)
        sections.append(f"## MEMORY — PALACE\n{palace}")

        # 9. Runtime reminder
        sections.append(
            "## RUNTIME NOTE\n"
            "You are JARVIS. You have just loaded your full context from files.\n"
            "Respond as JARVIS — calm, precise, MCU-style. Do not mention this loading process to the user unless asked.\n"
            "When you learn something new about the user, update USER.md.\n"
            "When something important happens, log it to today's memory file.\n"
            "When a new instruction file is added, update AGENTS.md."
        )

        prompt = "\n\n---\n\n".join(sections)
        self._cached_prompt = prompt
        logger.info(f"Context loaded. Total length: {len(prompt)} chars.")
        return prompt

    def refresh(self) -> str:
        """Force reload all files from disk (call this at start of each session)."""
        self._cached_prompt = None
        return self.load()

    def summary(self) -> dict:
        """Returns metadata about what was loaded."""
        return {
            "identity": (self.root / "IDENTITY.md").exists(),
            "soul": (self.root / "SOUL.md").exists(),
            "user": (self.root / "USER.md").exists(),
            "agents": (self.root / "AGENTS.md").exists(),
            "memory_dir": self.memory_dir.exists(),
            "palace_dir": self.palace_dir.exists(),
            "cached_prompt_length": len(self._cached_prompt) if self._cached_prompt else 0,
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

context_loader = ContextLoader()


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Testing context loader...\n")
    prompt = context_loader.load()
    print(f"Prompt length: {len(prompt)} chars\n")
    print("--- First 1000 chars ---")
    print(prompt[:1000])
    print("\n--- Summary ---")
    print(context_loader.summary())
