"""
tools/file_browser.py - JARVIS File Browser

Read, search, and navigate the filesystem.
Auto-registers with tool registry on import.

Usage:
    from tools.file_browser import file_browser
    content = file_browser.read("/home/user/notes.txt")
    results = file_browser.search("/home/user", "*.py")
    tree = file_browser.tree("/home/user/project")
"""

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger("jarvis.tools.files")


class FileBrowser:
    """Read and search the filesystem safely."""

    def __init__(self, safe_roots: list[str] = None):
        # Restrict to these directories for safety (None = unrestricted)
        self.safe_roots = [Path(r).expanduser() for r in (safe_roots or [])]

    def _is_safe(self, path: str) -> bool:
        if not self.safe_roots:
            return True
        p = Path(path).resolve()
        return any(str(p).startswith(str(r)) for r in self.safe_roots)

    def read(self, path: str, max_chars: int = 10000) -> str:
        """Read a text file. Returns content (truncated if large)."""
        if not self._is_safe(path):
            return f"Access denied: {path}"
        try:
            content = Path(path).read_text(encoding="utf-8", errors="replace")
            if len(content) > max_chars:
                content = content[:max_chars] + f"\n\n[...truncated at {max_chars} chars]"
            logger.debug(f"Read: {path}")
            return content
        except FileNotFoundError:
            return f"File not found: {path}"
        except Exception as e:
            return f"Error reading {path}: {e}"

    def search(self, directory: str, pattern: str = "*", max_results: int = 50) -> list[str]:
        """Search for files matching a glob pattern."""
        try:
            p = Path(directory).expanduser()
            results = [str(f) for f in p.rglob(pattern) if f.is_file()][:max_results]
            logger.debug(f"Search '{pattern}' in {directory} → {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def search_content(self, directory: str, keyword: str, pattern: str = "*.txt", max_results: int = 20) -> list[dict]:
        """Search file contents for a keyword."""
        results = []
        try:
            for fpath in Path(directory).expanduser().rglob(pattern):
                if len(results) >= max_results:
                    break
                try:
                    content = fpath.read_text(encoding="utf-8", errors="replace")
                    if keyword.lower() in content.lower():
                        # Find context around keyword
                        idx = content.lower().find(keyword.lower())
                        snippet = content[max(0, idx - 50):idx + 100].strip()
                        results.append({"file": str(fpath), "snippet": snippet})
                except Exception:
                    continue
        except Exception as e:
            logger.error(f"Content search error: {e}")
        return results

    def tree(self, directory: str, max_depth: int = 3, max_items: int = 100) -> str:
        """Generate a directory tree string."""
        try:
            lines = []
            count = 0

            def _walk(path: Path, prefix: str, depth: int):
                nonlocal count
                if depth > max_depth or count >= max_items:
                    return
                try:
                    items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
                except PermissionError:
                    return
                for i, item in enumerate(items):
                    if count >= max_items:
                        lines.append(f"{prefix}... (truncated)")
                        return
                    connector = "└── " if i == len(items) - 1 else "├── "
                    lines.append(f"{prefix}{connector}{item.name}")
                    count += 1
                    if item.is_dir():
                        extension = "    " if i == len(items) - 1 else "│   "
                        _walk(item, prefix + extension, depth + 1)

            p = Path(directory).expanduser()
            lines.append(str(p))
            _walk(p, "", 1)
            return "\n".join(lines)
        except Exception as e:
            return f"Error generating tree: {e}"

    def info(self, path: str) -> dict:
        """Get file/directory metadata."""
        try:
            p = Path(path).expanduser()
            stat = p.stat()
            return {
                "path": str(p),
                "exists": p.exists(),
                "is_file": p.is_file(),
                "is_dir": p.is_dir(),
                "size_bytes": stat.st_size if p.exists() else 0,
                "modified": stat.st_mtime if p.exists() else None,
            }
        except Exception as e:
            return {"path": path, "error": str(e)}

    def quick(self, path_or_query: str) -> str:
        """Smart handler for brain: read file or list directory."""
        p = Path(path_or_query).expanduser()
        if p.is_file():
            return self.read(str(p))
        elif p.is_dir():
            return self.tree(str(p))
        else:
            return f"Path not found: {path_or_query}"


# ---------------------------------------------------------------------------
# Singleton + auto-register
# ---------------------------------------------------------------------------

file_browser = FileBrowser()

from tools.registry import registry
registry.register(
    name="read_file",
    description="Read the contents of a file. Use when asked about file contents or local documents.",
    handler=lambda path, **_: file_browser.read(path),
    params={"path": "absolute file path to read"},
)
registry.register(
    name="list_directory",
    description="List files in a directory or show a directory tree.",
    handler=lambda path, **_: file_browser.tree(path),
    params={"path": "absolute directory path"},
)
registry.register(
    name="search_files",
    description="Search for files by name pattern in a directory.",
    handler=lambda directory, pattern="*", **_: "\n".join(file_browser.search(directory, pattern)),
    params={"directory": "directory to search", "pattern": "glob pattern e.g. *.py"},
)
