"""
system/self_repair.py - JARVIS Self Repair

Detects issues with JARVIS modules and attempts automatic recovery.
Monitors: Ollama, agents, task tracker, memory, senses.
Escalates to user if repair fails.

Usage:
    from system.self_repair import self_repair
    self_repair.start()
    self_repair.run_check()
"""

import logging
import threading
import time
from typing import Optional

logger = logging.getLogger("jarvis.self_repair")

CHECK_INTERVAL = 60   # seconds between health checks


class SelfRepair:
    """
    Monitors JARVIS module health and attempts fixes.
    """

    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._issues: list[dict] = []

    # ------------------------------------------------------------------
    # Health checks
    # ------------------------------------------------------------------

    def check_ollama(self) -> dict:
        """Check Ollama is reachable."""
        try:
            import requests
            from core.config_manager import config
            host = config.get("llm.ollama_host", "http://localhost:11434")
            r = requests.get(f"{host}/api/tags", timeout=3)
            r.raise_for_status()
            return {"ok": True, "component": "ollama"}
        except Exception as e:
            return {"ok": False, "component": "ollama", "error": str(e),
                    "fix": "ollama serve"}

    def check_memory(self) -> dict:
        """Check memory system is functional."""
        try:
            from core.jarvis import jarvis
            if jarvis.memory is None:
                return {"ok": False, "component": "memory", "error": "Memory not initialized"}
            jarvis.memory.log("self_repair health check", category="system")
            return {"ok": True, "component": "memory"}
        except Exception as e:
            return {"ok": False, "component": "memory", "error": str(e)}

    def check_task_tracker(self) -> dict:
        """Check task tracker is running."""
        try:
            from core.jarvis import jarvis
            if jarvis.tasks is None:
                return {"ok": False, "component": "task_tracker", "error": "Not initialized"}
            if not jarvis.tasks._running:
                return {"ok": False, "component": "task_tracker", "error": "Self-ping thread stopped",
                        "fix": "restart_task_tracker"}
            return {"ok": True, "component": "task_tracker"}
        except Exception as e:
            return {"ok": False, "component": "task_tracker", "error": str(e)}

    def check_agents(self) -> dict:
        """Check agent manager is running."""
        try:
            from core.jarvis import jarvis
            if jarvis.agents is None:
                return {"ok": False, "component": "agents", "error": "Not initialized"}
            if not jarvis.agents._running:
                return {"ok": False, "component": "agents", "error": "Monitor thread stopped",
                        "fix": "restart_agents"}
            return {"ok": True, "component": "agents"}
        except Exception as e:
            return {"ok": False, "component": "agents", "error": str(e)}

    def check_disk_space(self) -> dict:
        """Check available disk space."""
        try:
            import psutil
            disk = psutil.disk_usage("/")
            if disk.percent > 95:
                return {"ok": False, "component": "disk",
                        "error": f"Disk {disk.percent}% full ({disk.free // 1024**3}GB free)"}
            return {"ok": True, "component": "disk"}
        except Exception as e:
            return {"ok": False, "component": "disk", "error": str(e)}

    def run_all_checks(self) -> list[dict]:
        """Run all health checks. Returns list of issues."""
        checks = [
            self.check_ollama,
            self.check_memory,
            self.check_task_tracker,
            self.check_agents,
            self.check_disk_space,
        ]
        issues = []
        for check in checks:
            try:
                result = check()
                if not result["ok"]:
                    issues.append(result)
                    logger.warning(f"Health check failed: {result['component']} — {result.get('error', '')}")
            except Exception as e:
                logger.error(f"Check error: {e}")
        return issues

    # ------------------------------------------------------------------
    # Repair attempts
    # ------------------------------------------------------------------

    def attempt_repair(self, issue: dict) -> bool:
        """Try to fix an issue. Returns True if fixed."""
        component = issue.get("component")
        fix = issue.get("fix")

        logger.info(f"Attempting repair: {component} (fix: {fix})")

        if fix == "restart_task_tracker":
            try:
                from core.jarvis import jarvis
                jarvis.tasks.start()
                logger.info("Task tracker restarted.")
                return True
            except Exception as e:
                logger.error(f"Task tracker restart failed: {e}")

        elif fix == "restart_agents":
            try:
                from core.jarvis import jarvis
                jarvis.agents.start()
                logger.info("Agent manager restarted.")
                return True
            except Exception as e:
                logger.error(f"Agent manager restart failed: {e}")

        elif fix == "ollama serve":
            try:
                import subprocess
                subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(3)
                result = self.check_ollama()
                if result["ok"]:
                    logger.info("Ollama restarted successfully.")
                    return True
            except Exception as e:
                logger.error(f"Ollama restart failed: {e}")

        return False

    # ------------------------------------------------------------------
    # Run check cycle
    # ------------------------------------------------------------------

    def run_check(self):
        """Run a full check + repair cycle."""
        issues = self.run_all_checks()

        for issue in issues:
            self._issues.append({**issue, "time": time.time()})

            # Attempt repair
            fixed = self.attempt_repair(issue)

            # Report to user if not fixed
            if not fixed:
                msg = f"System issue detected: {issue['component']} — {issue.get('error', 'unknown error')}. Manual attention may be required."
                logger.error(msg)
                try:
                    from core.jarvis import jarvis
                    if jarvis.notifier:
                        jarvis.notifier.urgent(msg)
                    if jarvis.memory:
                        jarvis.memory.log(msg, category="error")
                except Exception:
                    pass

        if not issues:
            logger.debug("Self-repair: all systems nominal.")

        return issues

    # ------------------------------------------------------------------
    # Background loop
    # ------------------------------------------------------------------

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="self-repair")
        self._thread.start()
        logger.info(f"Self-repair monitor started (interval: {CHECK_INTERVAL}s)")

    def stop(self):
        self._running = False

    def _loop(self):
        time.sleep(30)   # wait for full boot before first check
        while self._running:
            try:
                self.run_check()
            except Exception as e:
                logger.error(f"Self-repair loop error: {e}")
            time.sleep(CHECK_INTERVAL)

    def status(self) -> dict:
        return {
            "running": self._running,
            "check_interval": CHECK_INTERVAL,
            "recent_issues": self._issues[-5:] if self._issues else [],
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

self_repair = SelfRepair()
