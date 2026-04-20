import json
import os
import logging
from enum import IntEnum
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger("jarvis.goals")

class GoalPriority(IntEnum):
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4

@dataclass
class Goal:
    name: str
    description: str
    priority: GoalPriority
    created_at: str = None
    status: str = "active"

class GoalManager:
    """
    Manages the persistent goals of the system (Kernel v2).
    Saves to memory/palace/goals.json.
    """

    def __init__(self, persistence_path: str = "memory/palace/goals.json"):
        self.path = persistence_path
        self.goals: List[Goal] = []
        self._load()
        
        if not self.goals:
            self._init_defaults()

    def _init_defaults(self):
        self.goals = [
            Goal("user_productivity", "Monitor for signs of being stuck or distracted; offer help.", GoalPriority.HIGH),
            Goal("system_harmony", "Ensure the system is not overheated or struggling for resources.", GoalPriority.CRITICAL),
            Goal("social_engagement", "Maintain a natural presence; avoid being too silent or too annoying.", GoalPriority.NORMAL),
            Goal("task_completion", "Nudge the user to finish active tasks and meet deadlines.", GoalPriority.HIGH)
        ]
        self._save()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, 'r') as f:
                    data = json.load(f)
                    self.goals = [Goal(**g) for g in data]
            except Exception as e:
                logger.error(f"Failed to load goals: {e}")

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, 'w') as f:
                json.dump([asdict(g) for g in self.goals], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save goals: {e}")

    def add_goal(self, name: str, description: str, priority: GoalPriority = GoalPriority.NORMAL):
        self.goals.append(Goal(name, description, priority))
        self._save()
        logger.info(f"New goal added: {name}")

    def remove_goal(self, name: str):
        self.goals = [g for g in self.goals if g.name != name]
        self._save()

    def get_summary(self) -> str:
        """Returns a string summary for brain context."""
        return "\n".join([f"- {g.name} ({g.priority.name}): {g.description}" for g in self.goals if g.status == "active"])

# Singleton
goal_manager = GoalManager()
