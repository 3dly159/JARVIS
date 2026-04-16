"""
skills/loader.py - JARVIS Skill Loader

Auto-discovers and loads all skills from the skills/ directory.
Supports three skill types:
  1. MD-only     — SKILL.md with instructions injected into brain context
  2. Python      — skill.py registers tools/actions with the registry
  3. ClawHub     — installed via clawhub CLI, same format as above

Usage:
    from skills.loader import skill_loader
    skill_loader.load_all()
    skill_loader.get_context()       # all skill instructions for brain
    skill_loader.list_skills()       # all loaded skills
"""

import importlib.util
import logging
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger("jarvis.skills")

SKILLS_DIR = Path(__file__).parent
SKILL_FILE = "SKILL.md"
SKILL_PY   = "skill.py"
SKILL_CFG  = "config.yaml"


class Skill:
    """Represents a single loaded skill."""

    def __init__(self, path: Path):
        self.path = path
        self.name = path.name
        self.instructions: str = ""       # from SKILL.md
        self.config: dict = {}            # from config.yaml
        self.has_code: bool = False       # has skill.py
        self.loaded: bool = False
        self.error: str = ""
        self.metadata: dict = {}          # parsed from SKILL.md frontmatter

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "path": str(self.path),
            "has_instructions": bool(self.instructions),
            "has_code": self.has_code,
            "loaded": self.loaded,
            "error": self.error,
            "description": self.metadata.get("description", ""),
            "version": self.metadata.get("version", ""),
        }

    def __repr__(self):
        return f"Skill({self.name}, loaded={self.loaded})"


class SkillLoader:
    """
    Discovers, loads, and manages JARVIS skills.
    Called at startup and when new skills are installed.
    """

    def __init__(self, skills_dir: Path = SKILLS_DIR):
        self.skills_dir = skills_dir
        self._skills: dict[str, Skill] = {}   # name → Skill

    # ------------------------------------------------------------------
    # Discovery + Load
    # ------------------------------------------------------------------

    def load_all(self) -> list[Skill]:
        """Scan skills/ directory and load all valid skills."""
        loaded = []
        if not self.skills_dir.exists():
            logger.warning(f"Skills directory not found: {self.skills_dir}")
            return []

        for item in sorted(self.skills_dir.iterdir()):
            # Skip non-directories and internal files
            if not item.is_dir():
                continue
            if item.name.startswith("_") or item.name == "__pycache__":
                continue

            skill = self._load_skill(item)
            if skill:
                self._skills[skill.name] = skill
                loaded.append(skill)

        logger.info(f"Skills loaded: {len(loaded)} ({[s.name for s in loaded]})")
        return loaded

    def _load_skill(self, path: Path) -> Optional[Skill]:
        """Load a single skill from its directory."""
        skill = Skill(path)

        # 1. Read SKILL.md (required)
        skill_md = path / SKILL_FILE
        if not skill_md.exists():
            logger.debug(f"Skipping {path.name} — no SKILL.md")
            return None

        try:
            raw = skill_md.read_text(encoding="utf-8")
            skill.instructions, skill.metadata = self._parse_skill_md(raw)
        except Exception as e:
            skill.error = f"SKILL.md parse error: {e}"
            logger.warning(f"Skill {path.name}: {skill.error}")

        # 2. Read config.yaml (optional)
        cfg_path = path / SKILL_CFG
        if cfg_path.exists():
            try:
                import yaml
                skill.config = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
            except Exception as e:
                logger.warning(f"Skill {path.name} config error: {e}")

        # 3. Load skill.py (optional)
        py_path = path / SKILL_PY
        if py_path.exists():
            skill.has_code = True
            try:
                self._load_python_skill(skill, py_path)
            except Exception as e:
                skill.error = f"skill.py load error: {e}"
                logger.error(f"Skill {path.name} Python error: {e}")

        skill.loaded = not bool(skill.error)
        if skill.loaded:
            logger.info(f"Skill loaded: {path.name}" + (" (with code)" if skill.has_code else " (MD only)"))
        return skill

    def _load_python_skill(self, skill: Skill, py_path: Path):
        """Import skill.py as a module."""
        module_name = f"skills.{skill.name}.skill"

        spec = importlib.util.spec_from_file_location(module_name, py_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Call register() if it exists
        if hasattr(module, "register"):
            module.register()
            logger.debug(f"Skill {skill.name}: register() called.")

    def _parse_skill_md(self, raw: str) -> tuple[str, dict]:
        """
        Parse SKILL.md — extract YAML frontmatter (if any) and body.
        Returns (instructions_text, metadata_dict).
        """
        metadata = {}
        content = raw

        # Strip YAML frontmatter (--- ... ---)
        if raw.startswith("---"):
            try:
                import yaml
                end = raw.index("---", 3)
                fm_raw = raw[3:end].strip()
                metadata = yaml.safe_load(fm_raw) or {}
                content = raw[end + 3:].strip()
            except Exception:
                pass   # No valid frontmatter — use full content

        return content, metadata

    # ------------------------------------------------------------------
    # Reload (called after installing new skills)
    # ------------------------------------------------------------------

    def reload(self) -> list[Skill]:
        """Reload all skills from disk."""
        self._skills.clear()
        return self.load_all()

    def load_one(self, skill_name: str) -> Optional[Skill]:
        """Load or reload a single skill by name."""
        path = self.skills_dir / skill_name
        if not path.exists():
            logger.warning(f"Skill directory not found: {skill_name}")
            return None
        skill = self._load_skill(path)
        if skill:
            self._skills[skill.name] = skill
        return skill

    # ------------------------------------------------------------------
    # Context for brain
    # ------------------------------------------------------------------

    def get_context(self) -> str:
        """
        Returns all skill instructions as a single block for brain injection.
        Each skill's SKILL.md content is included.
        """
        if not self._skills:
            return "No skills loaded."

        sections = ["## Installed Skills\n"]
        for skill in self._skills.values():
            if not skill.loaded or not skill.instructions:
                continue
            sections.append(f"### Skill: {skill.name}")
            if skill.metadata.get("description"):
                sections.append(f"*{skill.metadata['description']}*")
            sections.append(skill.instructions)
            sections.append("")

        return "\n".join(sections)

    def get_summary(self) -> str:
        """Short summary list of loaded skills for status displays."""
        if not self._skills:
            return "No skills installed."
        lines = ["Installed skills:"]
        for s in self._skills.values():
            status = "✓" if s.loaded else "✗"
            desc = s.metadata.get("description", "")
            code = " [+code]" if s.has_code else ""
            lines.append(f"  {status} {s.name}{code} — {desc}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def list_skills(self) -> list[dict]:
        return [s.to_dict() for s in self._skills.values()]

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def status(self) -> dict:
        return {
            "total": len(self._skills),
            "loaded": sum(1 for s in self._skills.values() if s.loaded),
            "with_code": sum(1 for s in self._skills.values() if s.has_code),
            "skills_dir": str(self.skills_dir),
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

skill_loader = SkillLoader()
