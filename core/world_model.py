"""
core/world_model.py - JARVIS World Model (Kernel v5)
Predictive simulation of user state and task environment.
Allows the kernel to 'pre-think' consequences of proactivity.
"""

import logging
import time
from typing import Dict, List, Optional
from core.cognition import CognitiveState

logger = logging.getLogger("jarvis.world")

class WorldModel:
    """
    Simulates user trajectory and context evolution.
    Implements 'State Transition Prediction'.
    """

    def __init__(self):
        self._history: List[CognitiveState] = []

    def update(self, current_state: CognitiveState):
        self._history.append(current_state)
        if len(self._history) > 50:
            self._history.pop(0)

    def predict_next_state(self, delta_t: float = 10.0) -> CognitiveState:
        """
        Predict what the next state will be if JARVIS does nothing.
        Uses linear extrapolation + heuristic decay.
        """
        if len(self._history) < 2:
            return CognitiveState()

        s1 = self._history[-2]
        s2 = self._history[-1]

        # Calculate deltas
        df = (s2.focus - s1.focus)
        de = (s2.energy - s1.energy)
        dp = (s2.progress - s1.progress)
        ds = (s2.stability - s1.stability)

        # Predict next value (clamped)
        pred = CognitiveState(
            focus=max(0.0, min(1.0, s2.focus + df)),
            energy=max(0.0, min(1.0, s2.energy + de)),
            progress=max(0.0, min(1.0, s2.progress + dp)),
            stability=max(0.0, min(1.0, s2.stability + ds)),
            user_present=s2.user_present,
            active_app=s2.active_app,
            idle_time=s2.idle_time + delta_t,
            switch_rate=s2.switch_rate
        )
        
        return pred

    def get_simulation_delta(self, action_consequence: float) -> float:
        """
        Estimate how an action will change the predicted state.
        Higher delta means 'Action is high impact'.
        """
        # Placeholder for more complex simulation
        return action_consequence * 0.5

# Singleton
world_model = WorldModel()
