"""
core/task_tracker.py - JARVIS Task Tracker

Creates, tracks, and self-pings tasks autonomously.
JARVIS builds task tracks, monitors progress, and ensures nothing stalls.
"""

import json
import logging
import threading
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional, Callable

logger = logging.getLogger("jarvis.task_tracker")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

TASKS_DIR = Path(__file__).parent.parent / "memory" / "tasks"


def _ensure_dirs():
    TASKS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Task Status
# ---------------------------------------------------------------------------

class TaskStatus(str, Enum):
    PENDING   = "pending"     # Created, not started
    ACTIVE    = "active"      # Currently being worked on
    STALLED   = "stalled"     # No progress for too long
    DONE      = "done"        # Completed successfully
    FAILED    = "failed"      # Could not complete
    CANCELLED = "cancelled"   # Manually cancelled


# ---------------------------------------------------------------------------
# Task Model
# ---------------------------------------------------------------------------

class Task:
    """Represents a single JARVIS task."""

    def __init__(
        self,
        title: str,
        description: str = "",
        steps: list[str] = None,
        priority: int = 5,          # 1 (highest) to 10 (lowest)
        deadline: Optional[str] = None,  # ISO datetime string
        task_id: Optional[str] = None,
    ):
        self.id = task_id or str(uuid.uuid4())[:8]
        self.title = title
        self.description = description
        self.steps = steps or []
        self.completed_steps: list[str] = []
        self.priority = priority
        self.status = TaskStatus.PENDING
        self.created = datetime.now().isoformat()
        self.updated = datetime.now().isoformat()
        self.last_pinged = datetime.now().isoformat()
        self.deadline = deadline
        self.notes: list[dict] = []   # progress notes with timestamps
        self.result: str = ""         # final result when done

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "steps": self.steps,
            "completed_steps": self.completed_steps,
            "priority": self.priority,
            "status": self.status.value,
            "created": self.created,
            "updated": self.updated,
            "last_pinged": self.last_pinged,
            "deadline": self.deadline,
            "notes": self.notes,
            "result": self.result,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        task = cls(
            title=data["title"],
            description=data.get("description", ""),
            steps=data.get("steps", []),
            priority=data.get("priority", 5),
            deadline=data.get("deadline"),
            task_id=data["id"],
        )
        task.completed_steps = data.get("completed_steps", [])
        task.status = TaskStatus(data.get("status", "pending"))
        task.created = data.get("created", task.created)
        task.updated = data.get("updated", task.updated)
        task.last_pinged = data.get("last_pinged", task.last_pinged)
        task.notes = data.get("notes", [])
        task.result = data.get("result", "")
        return task

    def add_note(self, note: str):
        self.notes.append({
            "time": datetime.now().isoformat(),
            "note": note,
        })
        self.updated = datetime.now().isoformat()
        self.last_pinged = datetime.now().isoformat()

    def complete_step(self, step: str):
        if step in self.steps and step not in self.completed_steps:
            self.completed_steps.append(step)
            self.updated = datetime.now().isoformat()
            self.last_pinged = datetime.now().isoformat()

    def progress_pct(self) -> int:
        if not self.steps:
            return 100 if self.status == TaskStatus.DONE else 0
        return int(len(self.completed_steps) / len(self.steps) * 100)

    def is_stalled(self, stall_minutes: int = 10) -> bool:
        if self.status not in (TaskStatus.ACTIVE, TaskStatus.PENDING):
            return False
        last = datetime.fromisoformat(self.last_pinged)
        return datetime.now() - last > timedelta(minutes=stall_minutes)

    def is_overdue(self) -> bool:
        if not self.deadline:
            return False
        return datetime.now() > datetime.fromisoformat(self.deadline)

    def __repr__(self):
        return f"Task({self.id}, '{self.title}', {self.status.value}, {self.progress_pct()}%)"


# ---------------------------------------------------------------------------
# Task Store
# ---------------------------------------------------------------------------

class TaskStore:
    """Persists tasks as JSON files in memory/tasks/."""

    def save(self, task: Task):
        _ensure_dirs()
        path = TASKS_DIR / f"{task.id}.json"
        path.write_text(json.dumps(task.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    def load(self, task_id: str) -> Optional[Task]:
        path = TASKS_DIR / f"{task_id}.json"
        if not path.exists():
            return None
        return Task.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def delete(self, task_id: str):
        path = TASKS_DIR / f"{task_id}.json"
        if path.exists():
            path.unlink()

    def load_all(self) -> list[Task]:
        _ensure_dirs()
        tasks = []
        for path in TASKS_DIR.glob("*.json"):
            try:
                tasks.append(Task.from_dict(json.loads(path.read_text(encoding="utf-8"))))
            except Exception as e:
                logger.error(f"Failed to load task {path.name}: {e}")
        return sorted(tasks, key=lambda t: (t.priority, t.created))

    def load_active(self) -> list[Task]:
        return [t for t in self.load_all() if t.status in (TaskStatus.ACTIVE, TaskStatus.PENDING)]


# ---------------------------------------------------------------------------
# Task Tracker
# ---------------------------------------------------------------------------

class TaskTracker:
    """
    JARVIS's autonomous task management system.
    - Creates and tracks tasks
    - Self-pings to check progress
    - Detects stalls and alerts
    - Notifies brain/user when something needs attention
    """

    def __init__(
        self,
        self_ping_interval: int = 60,       # seconds between self-pings
        stall_threshold: int = 10,          # minutes before a task is stalled
        on_stall: Optional[Callable] = None,     # callback(task) when stalled
        on_overdue: Optional[Callable] = None,   # callback(task) when overdue
        on_complete: Optional[Callable] = None,  # callback(task) when done
    ):
        self.store = TaskStore()
        self.self_ping_interval = self_ping_interval
        self.stall_threshold = stall_threshold
        self.on_stall = on_stall
        self.on_overdue = on_overdue
        self.on_complete = on_complete
        self._ping_thread: Optional[threading.Thread] = None
        self._running = False
        self._recent_completions: list[float] = [] # Timestamps of completions in last 24h
        logger.info("Task tracker online.")

    # ----- CRUD -----

    def create(
        self,
        title: str,
        description: str = "",
        steps: list[str] = None,
        priority: int = 5,
        deadline: Optional[str] = None,
    ) -> Task:
        """Create and persist a new task."""
        task = Task(title=title, description=description, steps=steps,
                    priority=priority, deadline=deadline)
        task.status = TaskStatus.ACTIVE
        self.store.save(task)
        logger.info(f"Task created: {task}")
        return task

    def get(self, task_id: str) -> Optional[Task]:
        return self.store.load(task_id)

    def list_all(self) -> list[Task]:
        return self.store.load_all()

    def list_active(self) -> list[Task]:
        return self.store.load_active()

    def update_status(self, task_id: str, status: TaskStatus, note: str = ""):
        task = self.store.load(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found.")
            return
        task.status = status
        if note:
            task.add_note(note)
        self.store.save(task)
        logger.info(f"Task {task_id} → {status.value}")

        if status == TaskStatus.DONE and self.on_complete:
            self.on_complete(task)

    def add_progress(self, task_id: str, note: str, step_done: str = ""):
        """Log progress on a task. Resets the stall timer."""
        task = self.store.load(task_id)
        if not task:
            return
        task.add_note(note)
        if step_done:
            task.complete_step(step_done)
        self.store.save(task)
        logger.debug(f"Progress on {task_id}: {note[:60]}")

    def complete(self, task_id: str, result: str = ""):
        """Mark a task as done."""
        task = self.store.load(task_id)
        if not task:
            return
        task.status = TaskStatus.DONE
        task.result = result
        task.updated = datetime.now().isoformat()
        self.store.save(task)
        self._recent_completions.append(time.time())
        logger.info(f"Task completed: {task_id} — {result[:60]}")
        if self.on_complete:
            self.on_complete(task)

    def get_completion_streak(self, window_hours: int = 4) -> int:
        """Returns number of tasks completed in the given window."""
        now = time.time()
        threshold = now - (window_hours * 3600)
        # Cleanup old ones
        self._recent_completions = [t for t in self._recent_completions if t > now - 86400]
        streak = sum(1 for t in self._recent_completions if t > threshold)
        return streak

    def cancel(self, task_id: str):
        self.update_status(task_id, TaskStatus.CANCELLED)

    # ----- Self-ping -----

    def ping(self) -> list[dict]:
        """
        JARVIS checks all active tasks.
        Returns list of alerts (stalled, overdue tasks).
        Called automatically by background thread.
        """
        alerts = []
        tasks = self.list_active()

        for task in tasks:
            # Check stall
            if task.is_stalled(self.stall_threshold):
                task.status = TaskStatus.STALLED
                self.store.save(task)
                alert = {
                    "type": "stalled",
                    "task_id": task.id,
                    "title": task.title,
                    "message": f"Task '{task.title}' has stalled — no progress in {self.stall_threshold} minutes.",
                }
                alerts.append(alert)
                logger.warning(f"STALLED: {task}")
                if self.on_stall:
                    self.on_stall(task)

            # Check overdue
            elif task.is_overdue():
                alert = {
                    "type": "overdue",
                    "task_id": task.id,
                    "title": task.title,
                    "message": f"Task '{task.title}' is overdue.",
                }
                alerts.append(alert)
                logger.warning(f"OVERDUE: {task}")
                if self.on_overdue:
                    self.on_overdue(task)

        if alerts:
            logger.info(f"Self-ping: {len(alerts)} alert(s) found.")
        else:
            logger.debug("Self-ping: all clear.")

        return alerts

    # ----- Background thread -----

    def start(self):
        """Start the background self-ping thread."""
        if self._running:
            return
        self._running = True
        self._ping_thread = threading.Thread(target=self._ping_loop, daemon=True)
        self._ping_thread.start()
        logger.info(f"Self-ping thread started (interval: {self.self_ping_interval}s)")

    def stop(self):
        """Stop the background self-ping thread."""
        self._running = False
        logger.info("Self-ping thread stopped.")

    def _ping_loop(self):
        while self._running:
            time.sleep(self.self_ping_interval)
            try:
                self.ping()
            except Exception as e:
                logger.error(f"Self-ping error: {e}")

    # ----- Summary for brain -----

    def summary(self) -> str:
        """Returns a text summary of active tasks for context injection."""
        tasks = self.list_active()
        if not tasks:
            return "No active tasks."
        lines = ["Active tasks:"]
        for t in tasks:
            overdue = " ⚠️ OVERDUE" if t.is_overdue() else ""
            stalled = " 🔴 STALLED" if t.status == TaskStatus.STALLED else ""
            lines.append(
                f"  [{t.id}] {t.title} | {t.progress_pct()}% | "
                f"priority {t.priority}{overdue}{stalled}"
            )
        return "\n".join(lines)

    def status(self) -> dict:
        all_tasks = self.list_all()
        return {
            "total": len(all_tasks),
            "active": len([t for t in all_tasks if t.status == TaskStatus.ACTIVE]),
            "pending": len([t for t in all_tasks if t.status == TaskStatus.PENDING]),
            "stalled": len([t for t in all_tasks if t.status == TaskStatus.STALLED]),
            "done": len([t for t in all_tasks if t.status == TaskStatus.DONE]),
            "failed": len([t for t in all_tasks if t.status == TaskStatus.FAILED]),
            "self_ping_interval": self.self_ping_interval,
            "running": self._running,
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

task_tracker = TaskTracker()


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Testing JARVIS task tracker...\n")

    # Create a task
    task = task_tracker.create(
        title="Build JARVIS brain module",
        description="Write and test core/brain.py",
        steps=["Write LLM wrapper", "Add streaming", "Add history", "Test"],
        priority=1,
    )
    print(f"Created: {task}")

    # Log progress
    task_tracker.add_progress(task.id, "LLM wrapper complete", step_done="Write LLM wrapper")
    task_tracker.add_progress(task.id, "Streaming implemented", step_done="Add streaming")

    # Check status
    t = task_tracker.get(task.id)
    print(f"Progress: {t.progress_pct()}% — steps done: {t.completed_steps}")

    # Complete it
    task_tracker.complete(task.id, result="brain.py written and tested successfully.")
    print(f"Final status: {task_tracker.get(task.id).status}")

    # Summary
    print("\nTracker status:", task_tracker.status())
    print("\nSummary:", task_tracker.summary())
