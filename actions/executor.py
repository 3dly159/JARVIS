"""
actions/executor.py - JARVIS Action Executor

Shell commands, file operations, process management.
All dangerous actions route through the confirmation gate first.

Usage:
    from actions.executor import executor
    result = executor.run("ls -la")
    executor.write_file("/tmp/note.txt", "hello")
    executor.delete_file("/tmp/note.txt")
"""

import logging
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger("jarvis.executor")


class Executor:
    """
    Safe command and file operation executor.
    Logs all actions to JARVIS memory.
    Routes dangerous operations through confirmation gate.
    """

    def __init__(self, timeout: int = 30, workdir: Optional[str] = None):
        self.timeout = timeout
        self.workdir = workdir or str(Path.home())

    # ------------------------------------------------------------------
    # Shell commands
    # ------------------------------------------------------------------

    def run(
        self,
        command: str,
        confirm: bool = True,
        capture: bool = True,
        workdir: Optional[str] = None,
    ) -> dict:
        """
        Run a shell command.
        Returns dict: {success, stdout, stderr, returncode, command}
        """
        if confirm:
            from actions.confirm import confirm as gate
            if not gate.request(f"Run command: {command}", action_type="shell_command"):
                return {"success": False, "stdout": "", "stderr": "Denied by user.", "returncode": -1, "command": command}

        logger.info(f"Executing: {command}")
        self._log_action(f"shell: {command}")

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=capture,
                text=True,
                timeout=self.timeout,
                cwd=workdir or self.workdir,
            )
            out = {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip() if capture else "",
                "stderr": result.stderr.strip() if capture else "",
                "returncode": result.returncode,
                "command": command,
            }
            if out["success"]:
                logger.info(f"Command succeeded: {command[:60]}")
            else:
                logger.warning(f"Command failed (rc={result.returncode}): {command[:60]}")
            return out

        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {command}")
            return {"success": False, "stdout": "", "stderr": "Timed out.", "returncode": -1, "command": command}
        except Exception as e:
            logger.error(f"Command error: {e}")
            return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1, "command": command}

    def run_safe(self, command: str, **kwargs) -> dict:
        """Run without confirmation (for trusted internal commands)."""
        return self.run(command, confirm=False, **kwargs)

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------

    def read_file(self, path: str) -> Optional[str]:
        """Read a text file. Returns content or None."""
        try:
            content = Path(path).read_text(encoding="utf-8")
            logger.debug(f"Read file: {path}")
            return content
        except Exception as e:
            logger.error(f"Read file error ({path}): {e}")
            return None

    def write_file(self, path: str, content: str, confirm: bool = False) -> bool:
        """Write content to a file."""
        if confirm:
            from actions.confirm import confirm as gate
            if not gate.request(f"Write to file: {path}", action_type="file_write"):
                return False

        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            self._log_action(f"write_file: {path}")
            logger.info(f"File written: {path}")
            return True
        except Exception as e:
            logger.error(f"Write file error ({path}): {e}")
            return False

    def append_file(self, path: str, content: str) -> bool:
        """Append content to a file."""
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(content)
            logger.debug(f"Appended to: {path}")
            return True
        except Exception as e:
            logger.error(f"Append file error: {e}")
            return False

    def delete_file(self, path: str, confirm: bool = True) -> bool:
        """Delete a file. Requires confirmation by default."""
        if confirm:
            from actions.confirm import confirm as gate
            if not gate.request(f"Delete file: {path}", action_type="file_delete"):
                return False
        try:
            Path(path).unlink(missing_ok=True)
            self._log_action(f"delete_file: {path}")
            logger.info(f"File deleted: {path}")
            return True
        except Exception as e:
            logger.error(f"Delete file error: {e}")
            return False

    def copy_file(self, src: str, dst: str) -> bool:
        """Copy a file."""
        try:
            shutil.copy2(src, dst)
            logger.info(f"Copied: {src} → {dst}")
            return True
        except Exception as e:
            logger.error(f"Copy error: {e}")
            return False

    def move_file(self, src: str, dst: str, confirm: bool = False) -> bool:
        """Move a file."""
        if confirm:
            from actions.confirm import confirm as gate
            if not gate.request(f"Move {src} → {dst}", action_type="file_move"):
                return False
        try:
            shutil.move(src, dst)
            self._log_action(f"move_file: {src} → {dst}")
            logger.info(f"Moved: {src} → {dst}")
            return True
        except Exception as e:
            logger.error(f"Move error: {e}")
            return False

    def list_dir(self, path: str = ".") -> list[str]:
        """List directory contents."""
        try:
            return [str(p) for p in Path(path).iterdir()]
        except Exception as e:
            logger.error(f"List dir error: {e}")
            return []

    def make_dir(self, path: str) -> bool:
        """Create directory (and parents)."""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Make dir error: {e}")
            return False

    # ------------------------------------------------------------------
    # Process management
    # ------------------------------------------------------------------

    def open_app(self, app: str) -> bool:
        """Open an application."""
        result = self.run_safe(f"xdg-open '{app}' &" if os.name != "nt" else f"start '{app}'")
        return result["success"]

    def kill_process(self, name: str, confirm: bool = True) -> bool:
        """Kill a process by name."""
        if confirm:
            from actions.confirm import confirm as gate
            if not gate.request(f"Kill process: {name}", action_type="shell_command"):
                return False
        result = self.run_safe(f"pkill -f '{name}'")
        return result["success"]

    def get_processes(self) -> list[dict]:
        """Get running processes."""
        try:
            import psutil
            return [
                {"pid": p.pid, "name": p.name(), "status": p.status()}
                for p in psutil.process_iter(["pid", "name", "status"])
            ]
        except ImportError:
            result = self.run_safe("ps aux")
            return [{"raw": result["stdout"]}]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _log_action(self, action: str):
        try:
            from core.jarvis import jarvis
            if jarvis.memory:
                jarvis.memory.log_action(action)
        except Exception:
            pass

    def status(self) -> dict:
        return {
            "timeout": self.timeout,
            "workdir": self.workdir,
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

executor = Executor()
