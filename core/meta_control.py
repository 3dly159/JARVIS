"""
core/meta_control.py - JARVIS Meta-Control (Kernel v6/v7)
Autonomous management of the cognitive architecture itself.
Detects state drift and corrects behavioral biases.
"""

import logging
from typing import Dict, List, Optional
from core.cognition import CognitiveState, CognitivePolicy

logger = logging.getLogger("jarvis.meta")

class MetaControl:
    """
    The 'Watchman' of the Cognitive Kernel.
    Ensures policy adjustments are effective.
    """

    def __init__(self):
        self._drift_history: List[float] = []

    def evaluate_efficiency(self, state: CognitiveState, policy: CognitivePolicy):
        """
        Detects if the current policy is 'Drifting' from optimal.
        Example: High focus protection + User frustration = BAD DRIFT.
        """
        drift = 0.0
        
        # Conflict: High Focus Protection but Low Progress
        if policy.focus_protection and state.progress < 0.3:
            drift += 0.4
            
        # Conflict: Silent suppression while in 'Need Help' state
        if policy.suppress_low_priority and state.energy > 0.8 and state.switch_rate > 0.7:
            drift += 0.5

        if drift > 0.3:
            logger.warning(f"Cognitive Drift Detected: {drift:.2f}. Meta-correction triggered.")
            # Trigger bias correction (e.g., lower threshold scale)
            policy.threshold_scale *= 0.8
            
        self._drift_history.append(drift)
        if len(self._drift_history) > 100:
            self._drift_history.pop(0)

    def get_summary(self) -> str:
        avg_drift = sum(self._drift_history) / len(self._drift_history) if self._drift_history else 0
        return f"Control Stability: {'Optimal' if avg_drift < 0.2 else 'Stabilizing'}"

# Singleton
meta_control = MetaControl()
