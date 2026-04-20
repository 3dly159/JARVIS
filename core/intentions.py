"""
core/intentions.py - JARVIS Intention Engine (Kernel v2)
Tracks user 'unspoken' intent based on app context, task data, and session history.
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from core.state_compressor import CognitiveState

logger = logging.getLogger("jarvis.intentions")

@dataclass
class Intention:
    label: str
    confidence: float
    context: str
    target_goal: Optional[str] = None

class IntentionEngine:
    """
    Captures the 'Why' behind user actions.
    Helps the kernel decide if an interruption aligns with user intent.
    """

    def __init__(self):
        self.current_intentions: List[Intention] = []
        self._history: List[Intention] = []

    def update(self, state: "CognitiveState"):
        """Heuristically derive intentions from state."""
        new_intentions = []
        
        # 1. Coding intent
        if "VSCode" in state.active_app or "Terminal" in state.active_app:
            if state.focus > 0.7:
                new_intentions.append(Intention("deep_work", 0.9, "Focused on technical execution", "user_productivity"))
            elif state.switch_rate > 0.5:
                new_intentions.append(Intention("debugging_loop", 0.7, "Rapidly switching between context", "task_completion"))
        
        # 2. Idle / Discovery intent
        if state.idle_time > 120:
             new_intentions.append(Intention("passive_discovery", 0.5, "User is idle; might be open to suggestions", "social_engagement"))

        self.current_intentions = new_intentions
        logger.debug(f"Intentions updated: {[i.label for i in self.current_intentions]}")

    def get_summary(self) -> str:
        if not self.current_intentions:
            return "Indeterminate (Stable passive state)"
        return ", ".join([f"{i.label} ({i.confidence:.1f})" for i in self.current_intentions])

# Singleton
intent_engine = IntentionEngine()
