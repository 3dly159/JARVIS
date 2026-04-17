"""
tools/web_search.py - JARVIS Web Search

DuckDuckGo search — no API key required, fully local.
Auto-registers with tool registry on import.

Usage:
    from tools.web_search import search
    results = search.query("latest Python news")
    snippet = search.quick(query)   # single-string result for brain
"""

import logging
from typing import Optional

logger = logging.getLogger("jarvis.tools.search")


class WebSearch:
    """DuckDuckGo search wrapper (using ddgs)."""

    def __init__(self, max_results: int = 5):
        self.max_results = max_results

    def query(self, query: str, max_results: Optional[int] = None) -> list[dict]:
        """
        Search DuckDuckGo. Returns list of {title, url, body} dicts.
        """
        try:
            from ddgs import DDGS
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results or self.max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "body": r.get("body", ""),
                    })
            logger.info(f"Search '{query[:40]}' → {len(results)} results")
            return results
        except ImportError:
            logger.error("ddgs not installed. Run: pip install ddgs")
            return []
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def quick(self, query: str) -> str:
        """
        Search and return a formatted string for brain consumption.
        """
        results = self.query(query)
        if not results:
            return f"No results found for: {query}"

        lines = [f"Search results for '{query}':\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. {r['title']}")
            lines.append(f"   {r['url']}")
            if r["body"]:
                lines.append(f"   {r['body'][:200]}")
            lines.append("")
        return "\n".join(lines)

    def news(self, query: str, max_results: int = 5) -> list[dict]:
        """Search recent news."""
        try:
            from ddgs import DDGS
            results = []
            with DDGS() as ddgs:
                for r in ddgs.news(query, max_results=max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "body": r.get("body", ""),
                        "date": r.get("date", ""),
                        "source": r.get("source", ""),
                    })
            return results
        except Exception as e:
            logger.error(f"News search error: {e}")
            return []


# ---------------------------------------------------------------------------
# Singleton + auto-register
# ---------------------------------------------------------------------------

search = WebSearch()

from tools.registry import registry
registry.register(
    name="web_search",
    description="Search the web for information. Use for current events, facts, or anything not in memory.",
    handler=lambda query, **_: search.quick(query),
    params={"query": "search query string"},
)
