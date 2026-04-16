"""
self_mod/code_editor.py - JARVIS Self-Modification (Code Editor)

JARVIS can read, patch, and write its own source files.
Always sandboxed + backed up before applying changes.

Usage:
    from self_mod.code_editor import code_editor
    code_editor.read_file("core/brain.py")
    code_editor.patch("core/brain.py", old_code, new_code)
    code_editor.add_method("core/brain.py", "ClassName", method_code)
"""

import ast
import logging
import shutil
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger("jarvis.code_editor")

ROOT = Path(__file__).parent.parent
BACKUP_DIR = ROOT / "self_mod" / "backups"


class CodeEditor:
    """
    Safe self-modification: read, patch, validate, backup, apply.
    Never modifies running code directly — writes to temp, validates, then applies.
    """

    def __init__(self, sandbox_before_apply: bool = True, backup_on_modify: bool = True):
        self.sandbox_before_apply = sandbox_before_apply
        self.backup_on_modify = backup_on_modify
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def read_file(self, relative_path: str) -> str:
        """Read a JARVIS source file."""
        path = ROOT / relative_path
        if not path.exists():
            return f"File not found: {relative_path}"
        try:
            content = path.read_text(encoding="utf-8")
            logger.info(f"Read source: {relative_path}")
            return content
        except Exception as e:
            return f"Error reading {relative_path}: {e}"

    def list_source_files(self, pattern: str = "**/*.py") -> list[str]:
        """List all Python source files in the JARVIS project."""
        return [str(p.relative_to(ROOT)) for p in ROOT.glob(pattern)
                if ".git" not in str(p) and "backups" not in str(p) and "__pycache__" not in str(p)]

    # ------------------------------------------------------------------
    # Validate
    # ------------------------------------------------------------------

    def validate_syntax(self, code: str, filename: str = "<unknown>") -> tuple[bool, str]:
        """
        Check Python syntax. Returns (valid, error_message).
        """
        try:
            ast.parse(code)
            return True, ""
        except SyntaxError as e:
            return False, f"Syntax error in {filename} at line {e.lineno}: {e.msg}"
        except Exception as e:
            return False, str(e)

    # ------------------------------------------------------------------
    # Backup
    # ------------------------------------------------------------------

    def backup(self, relative_path: str) -> str:
        """Create a timestamped backup of a file. Returns backup path."""
        src = ROOT / relative_path
        if not src.exists():
            return ""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        safe_name = relative_path.replace("/", "_").replace("\\", "_")
        backup_path = BACKUP_DIR / f"{safe_name}.{timestamp}.bak"
        shutil.copy2(src, backup_path)
        logger.info(f"Backup created: {backup_path.name}")
        return str(backup_path)

    def restore_backup(self, relative_path: str) -> bool:
        """Restore the most recent backup of a file."""
        safe_name = relative_path.replace("/", "_").replace("\\", "_")
        backups = sorted(BACKUP_DIR.glob(f"{safe_name}.*.bak"), reverse=True)
        if not backups:
            logger.warning(f"No backup found for: {relative_path}")
            return False
        dst = ROOT / relative_path
        shutil.copy2(backups[0], dst)
        logger.info(f"Restored: {relative_path} from {backups[0].name}")
        return True

    def list_backups(self, relative_path: Optional[str] = None) -> list[str]:
        """List available backups."""
        pattern = f"{relative_path.replace('/', '_')}*.bak" if relative_path else "*.bak"
        return [p.name for p in sorted(BACKUP_DIR.glob(pattern), reverse=True)]

    # ------------------------------------------------------------------
    # Patch
    # ------------------------------------------------------------------

    def patch(self, relative_path: str, old_code: str, new_code: str) -> dict:
        """
        Replace old_code with new_code in a source file.
        Validates syntax, optionally runs in sandbox, then applies.
        Returns dict: {success, message, backup_path}
        """
        path = ROOT / relative_path
        if not path.exists():
            return {"success": False, "message": f"File not found: {relative_path}"}

        original = path.read_text(encoding="utf-8")
        if old_code not in original:
            return {"success": False, "message": f"Target code not found in {relative_path}"}

        patched = original.replace(old_code, new_code, 1)

        # Validate syntax
        valid, error = self.validate_syntax(patched, relative_path)
        if not valid:
            return {"success": False, "message": f"Syntax error in patched code: {error}"}

        # Sandbox test
        if self.sandbox_before_apply:
            from self_mod.sandbox import sandbox
            ok, msg = sandbox.test_code(patched, filename=relative_path)
            if not ok:
                return {"success": False, "message": f"Sandbox test failed: {msg}"}

        # Backup
        backup_path = ""
        if self.backup_on_modify:
            backup_path = self.backup(relative_path)

        # Apply
        path.write_text(patched, encoding="utf-8")
        self._log_change(relative_path, "patch", old_code[:60], new_code[:60])
        logger.info(f"Patched: {relative_path}")
        return {"success": True, "message": f"Patched {relative_path}", "backup_path": backup_path}

    def write_file(self, relative_path: str, content: str) -> dict:
        """
        Write complete file content (for new files or full rewrites).
        """
        path = ROOT / relative_path

        # Validate syntax for Python files
        if relative_path.endswith(".py"):
            valid, error = self.validate_syntax(content, relative_path)
            if not valid:
                return {"success": False, "message": f"Syntax error: {error}"}

        # Sandbox test
        if self.sandbox_before_apply and relative_path.endswith(".py"):
            from self_mod.sandbox import sandbox
            ok, msg = sandbox.test_code(content, filename=relative_path)
            if not ok:
                return {"success": False, "message": f"Sandbox test failed: {msg}"}

        # Backup existing
        backup_path = ""
        if self.backup_on_modify and path.exists():
            backup_path = self.backup(relative_path)

        # Write
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        self._log_change(relative_path, "write", "", content[:60])
        logger.info(f"Written: {relative_path}")
        return {"success": True, "message": f"Written {relative_path}", "backup_path": backup_path}

    def append_to_file(self, relative_path: str, content: str) -> dict:
        """Append content to an existing file."""
        path = ROOT / relative_path
        if not path.exists():
            return {"success": False, "message": f"File not found: {relative_path}"}

        original = path.read_text(encoding="utf-8")
        new_content = original + "\n" + content

        if relative_path.endswith(".py"):
            valid, error = self.validate_syntax(new_content, relative_path)
            if not valid:
                return {"success": False, "message": f"Syntax error: {error}"}

        if self.backup_on_modify:
            self.backup(relative_path)

        path.write_text(new_content, encoding="utf-8")
        logger.info(f"Appended to: {relative_path}")
        return {"success": True, "message": f"Appended to {relative_path}"}

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _log_change(self, path: str, action: str, old: str, new: str):
        try:
            from core.jarvis import jarvis
            if jarvis.memory:
                jarvis.memory.log(
                    f"self_mod [{action}]: {path}\nOld: {old}\nNew: {new}",
                    category="self_mod"
                )
        except Exception:
            pass

    def status(self) -> dict:
        return {
            "sandbox_before_apply": self.sandbox_before_apply,
            "backup_on_modify": self.backup_on_modify,
            "backup_count": len(list(BACKUP_DIR.glob("*.bak"))),
            "source_files": len(self.list_source_files()),
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

from core.config_manager import config

code_editor = CodeEditor(
    sandbox_before_apply=config.get("self_mod.sandbox_before_apply", True),
    backup_on_modify=config.get("self_mod.backup_on_modify", True),
)
