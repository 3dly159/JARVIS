"""
skills/manager.py - JARVIS Skills Manager

ClawHub CLI integration + skill lifecycle management.
JARVIS can search, install, update, and remove skills via natural language
or directly through this module.

Usage:
    from skills.manager import skill_manager
    skill_manager.search("home automation")
    skill_manager.install("home-automation")
    skill_manager.update("home-automation")
    skill_manager.update_all()
    skill_manager.remove("home-automation")
    skill_manager.list_installed()
"""

import logging
import subprocess
import shutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger("jarvis.skills.manager")

SKILLS_DIR = Path(__file__).parent
CLAWHUB_BIN = "clawhub"


class SkillManager:
    """
    Manages skill installation via ClawHub CLI.
    Wraps the `clawhub` command and keeps skill_loader in sync.
    """

    def __init__(self, skills_dir: Path = SKILLS_DIR):
        self.skills_dir = skills_dir
        self._clawhub_available = self._check_clawhub()

    # ------------------------------------------------------------------
    # ClawHub availability
    # ------------------------------------------------------------------

    def _check_clawhub(self) -> bool:
        available = shutil.which(CLAWHUB_BIN) is not None
        if available:
            logger.info("ClawHub CLI found.")
        else:
            logger.warning("ClawHub CLI not found. Run: npm install -g clawhub")
        return available

    def _run(self, args: list[str], capture: bool = True) -> dict:
        """Run a clawhub command. Returns {success, stdout, stderr}."""
        if not self._clawhub_available:
            return {"success": False, "stdout": "", "stderr": "ClawHub CLI not installed. Run: npm install -g clawhub"}

        cmd = [CLAWHUB_BIN] + args
        logger.debug(f"Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd,
                capture_output=capture,
                text=True,
                timeout=60,
                cwd=str(self.skills_dir.parent),  # run from JARVIS root
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip() if capture else "",
                "stderr": result.stderr.strip() if capture else "",
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "stdout": "", "stderr": "Command timed out."}
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e)}

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query: str) -> str:
        """
        Search ClawHub for skills matching a query.
        Returns formatted results string.
        """
        logger.info(f"Searching ClawHub: {query}")
        result = self._run(["search", query])
        if result["success"]:
            return result["stdout"] or f"No results found for: {query}"
        return f"Search failed: {result['stderr']}"

    # ------------------------------------------------------------------
    # Install
    # ------------------------------------------------------------------

    def install(self, skill_name: str, version: Optional[str] = None) -> dict:
        """
        Install a skill from ClawHub.
        Returns {success, message, skill_name}
        """
        args = ["install", skill_name, "--dir", str(self.skills_dir)]
        if version:
            args += ["--version", version]

        logger.info(f"Installing skill: {skill_name}")
        result = self._run(args)

        if result["success"]:
            # Reload skill_loader so new skill is available immediately
            self._reload_skill(skill_name)
            msg = f"Skill '{skill_name}' installed successfully."
            logger.info(msg)
            self._log(f"Installed skill: {skill_name}")
        else:
            msg = f"Failed to install '{skill_name}': {result['stderr']}"
            logger.error(msg)

        return {
            "success": result["success"],
            "message": msg,
            "skill_name": skill_name,
            "output": result["stdout"],
        }

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, skill_name: str, version: Optional[str] = None, force: bool = False) -> dict:
        """Update a specific skill to latest (or specified version)."""
        args = ["update", skill_name, "--dir", str(self.skills_dir)]
        if version:
            args += ["--version", version]
        if force:
            args.append("--force")

        logger.info(f"Updating skill: {skill_name}")
        result = self._run(args)

        if result["success"]:
            self._reload_skill(skill_name)
            msg = f"Skill '{skill_name}' updated."
            self._log(f"Updated skill: {skill_name}")
        else:
            msg = f"Update failed for '{skill_name}': {result['stderr']}"

        return {"success": result["success"], "message": msg, "output": result["stdout"]}

    def update_all(self, force: bool = False) -> dict:
        """Update all installed ClawHub skills."""
        args = ["update", "--all", "--dir", str(self.skills_dir), "--no-input"]
        if force:
            args.append("--force")

        logger.info("Updating all skills...")
        result = self._run(args)

        if result["success"]:
            from skills.loader import skill_loader
            skill_loader.reload()
            msg = "All skills updated."
            self._log("Updated all skills")
        else:
            msg = f"Update all failed: {result['stderr']}"

        return {"success": result["success"], "message": msg, "output": result["stdout"]}

    # ------------------------------------------------------------------
    # Remove
    # ------------------------------------------------------------------

    def remove(self, skill_name: str) -> dict:
        """Remove an installed skill."""
        skill_path = self.skills_dir / skill_name
        if not skill_path.exists():
            return {"success": False, "message": f"Skill '{skill_name}' not found."}

        try:
            import shutil as sh
            sh.rmtree(skill_path)

            # Remove from loader
            from skills.loader import skill_loader
            skill_loader._skills.pop(skill_name, None)

            msg = f"Skill '{skill_name}' removed."
            self._log(f"Removed skill: {skill_name}")
            logger.info(msg)
            return {"success": True, "message": msg}
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    def list_installed(self) -> list[dict]:
        """List all installed skills (from loader)."""
        from skills.loader import skill_loader
        return skill_loader.list_skills()

    def list_clawhub(self) -> str:
        """List skills tracked by ClawHub CLI."""
        result = self._run(["list"])
        return result["stdout"] if result["success"] else f"Error: {result['stderr']}"

    # ------------------------------------------------------------------
    # Create local skill
    # ------------------------------------------------------------------

    def create_local(self, name: str, description: str = "", with_python: bool = False) -> dict:
        """
        Create a new local skill directory with SKILL.md template.
        """
        skill_path = self.skills_dir / name
        if skill_path.exists():
            return {"success": False, "message": f"Skill '{name}' already exists."}

        try:
            skill_path.mkdir(parents=True)

            # Write SKILL.md
            skill_md = f"""---
name: {name}
description: {description or name}
version: "1.0.0"
author: JARVIS
---

# {name}

{description or 'Describe what this skill does.'}

## Instructions

<!-- Add instructions for JARVIS here.
     JARVIS will read this file and follow these instructions
     when this skill is relevant to the conversation. -->

## Commands

<!-- List commands or actions this skill enables. -->
"""
            (skill_path / "SKILL.md").write_text(skill_md, encoding="utf-8")

            # Write skill.py stub if requested
            if with_python:
                py_stub = f'''"""
skills/{name}/skill.py

Python implementation for the {name} skill.
"""
from tools.registry import registry


def register():
    """Called by skill_loader when this skill is loaded."""
    registry.register(
        name="{name.replace("-", "_")}",
        description="{description or name}",
        handler=lambda **kwargs: "Not implemented yet.",
        params={{}},
    )
'''
                (skill_path / "skill.py").write_text(py_stub, encoding="utf-8")

            # Load the new skill
            from skills.loader import skill_loader
            skill = skill_loader.load_one(name)

            msg = f"Skill '{name}' created at {skill_path}"
            self._log(f"Created local skill: {name}")
            logger.info(msg)
            return {"success": True, "message": msg, "path": str(skill_path)}

        except Exception as e:
            return {"success": False, "message": str(e)}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _reload_skill(self, skill_name: str):
        """Reload a single skill after install/update."""
        try:
            from skills.loader import skill_loader
            skill_loader.load_one(skill_name)
        except Exception as e:
            logger.warning(f"Could not reload skill {skill_name}: {e}")

    def _log(self, msg: str):
        try:
            from core.jarvis import jarvis
            if jarvis.memory:
                jarvis.memory.log(msg, category="skills")
        except Exception:
            pass

    def status(self) -> dict:
        return {
            "clawhub_available": self._clawhub_available,
            "skills_dir": str(self.skills_dir),
            "installed": len(self.list_installed()),
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

skill_manager = SkillManager()
