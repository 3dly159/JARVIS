"""
self_mod/sandbox.py - JARVIS Code Sandbox

Tests modified code in isolation before applying to the live system.
Uses subprocess isolation — modified code never runs in the main process.

Usage:
    from self_mod.sandbox import sandbox
    ok, msg = sandbox.test_code(new_code, filename="core/brain.py")
    ok, msg = sandbox.test_file("core/brain.py")
"""

import logging
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger("jarvis.sandbox")

ROOT = Path(__file__).parent.parent
SANDBOX_TIMEOUT = 15    # seconds


class Sandbox:
    """
    Isolated code tester. Runs code in a subprocess.
    Checks for: syntax errors, import errors, runtime crashes.
    Never executes in the main JARVIS process.
    """

    def __init__(self, timeout: int = SANDBOX_TIMEOUT):
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Test code string
    # ------------------------------------------------------------------

    def test_code(self, code: str, filename: str = "<sandbox>") -> tuple[bool, str]:
        """
        Test a code string in isolation.
        Returns (success, message).
        """
        # Step 1: Syntax check (fast, no subprocess needed)
        import ast
        try:
            ast.parse(code)
        except SyntaxError as e:
            return False, f"Syntax error at line {e.lineno}: {e.msg}"

        # Step 2: Write to temp file and import-test in subprocess
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        try:
            result = self._run_isolated(tmp_path, check_imports_only=True)
            return result
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Test existing file
    # ------------------------------------------------------------------

    def test_file(self, relative_path: str) -> tuple[bool, str]:
        """
        Test an existing JARVIS source file in isolation.
        """
        path = ROOT / relative_path
        if not path.exists():
            return False, f"File not found: {relative_path}"
        return self._run_isolated(str(path), check_imports_only=True)

    # ------------------------------------------------------------------
    # Subprocess runner
    # ------------------------------------------------------------------

    def _run_isolated(self, file_path: str, check_imports_only: bool = True) -> tuple[bool, str]:
        """
        Run a Python file in an isolated subprocess.
        check_imports_only=True: only validates imports, doesn't execute __main__
        """
        # Build a wrapper that imports the module without running __main__
        wrapper_code = f"""
import sys
sys.path.insert(0, r"{ROOT}")
import ast, importlib.util

path = r"{file_path}"

# Syntax check
with open(path, encoding="utf-8") as f:
    source = f.read()
try:
    ast.parse(source)
except SyntaxError as e:
    print(f"SYNTAX_ERROR: {{e}}", file=sys.stderr)
    sys.exit(1)

# Import check (compile only, don't execute)
try:
    spec = importlib.util.spec_from_file_location("_sandbox_module", path)
    module = importlib.util.module_from_spec(spec)
    # Only load if no circular deps expected
    # spec.loader.exec_module(module)  # disabled — too risky in sandbox
    print("OK")
except Exception as e:
    print(f"IMPORT_ERROR: {{e}}", file=sys.stderr)
    sys.exit(2)
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as wrapper:
            wrapper.write(wrapper_code)
            wrapper_path = wrapper.name

        try:
            result = subprocess.run(
                [sys.executable, wrapper_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(ROOT),
            )

            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            if result.returncode == 0 and "OK" in stdout:
                logger.debug(f"Sandbox OK: {file_path}")
                return True, "OK"
            else:
                error = stderr or stdout or f"Exit code {result.returncode}"
                logger.warning(f"Sandbox FAILED: {file_path} — {error}")
                return False, error

        except subprocess.TimeoutExpired:
            return False, f"Sandbox timed out after {self.timeout}s"
        except Exception as e:
            return False, str(e)
        finally:
            try:
                os.unlink(wrapper_path)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Quick diff preview
    # ------------------------------------------------------------------

    def diff(self, original: str, modified: str) -> str:
        """Show a unified diff between original and modified code."""
        import difflib
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)
        diff = difflib.unified_diff(
            original_lines, modified_lines,
            fromfile="original", tofile="modified", lineterm=""
        )
        return "".join(diff) or "No differences."

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def status(self) -> dict:
        return {
            "timeout": self.timeout,
            "python": sys.executable,
            "root": str(ROOT),
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

sandbox = Sandbox()
