"""
core/state_compressor.py - JARVIS State Compression Layer
Aggregates sensory input into a unified Cognitive State Vector (CSV).
"""

import time
import math
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional

logger = logging.getLogger("jarvis.state")

@dataclass
class CognitiveState:
    """Unified Cognitive State Vector (Pure v8)"""
    # 4 Core Continuous Variables (0.0 to 1.0)
    focus: float = 0.5      # Clarity - Noise
    energy: float = 0.5     # Interaction Intensity
    progress: float = 0.5   # Task Velocity
    stability: float = 0.5  # Pattern Consistency
    
    # Derivations
    momentum: float = 0.5
    saliency: float = 0.0   # Difference from baseline
    
    # Metadata
    active_app: str = "Unknown"
    idle_time: float = 0.0
    switch_rate: float = 0.0
    user_present: bool = True
    
    # Active states (for backwards compatibility/labels)
    active_labels: Set[str] = field(default_factory=set)

class StateCompressor:
    """
    Transforms raw sensory data into a high-dimensional vector.
    Eliminates rule-based triggers in favor of continuous metrics.
    """

    def __init__(self):
        self._app_history: List[str] = []
        self._max_history = 15
        self._last_interaction = time.time()
        self._last_vector: Optional[CognitiveState] = None

    def compress(self) -> CognitiveState:
        """The core Perception -> Compression step."""
        from core.jarvis import jarvis
        now = time.time()
        
        # 1. RAW SENSORY INPUT
        idle_time = now - self._last_interaction
        active_app = self._detect_active_app()
        self._app_history.append(active_app)
        if len(self._app_history) > self._max_history:
            self._app_history.pop(0)

        # 2. SIGNAL PROCESSING
        switches = sum(1 for i in range(1, len(self._app_history)) if self._app_history[i] != self._app_history[i-1])
        switch_freq = switches / len(self._app_history) if len(self._app_history) > 1 else 0
        
        # 3. VECTOR CALCULATION (v8 Logic)
        # FOCUS: app relevance + switching noise
        app_weight = 1.0 if any(w in active_app.lower() for w in ["code", "term", "doc", "web"]) else 0.4
        focus_score = app_weight * (1.0 - (switch_freq * 1.5))
        
        # ENERGY: interaction recency
        last_voice = jarvis.ears.get_last_interaction_time() if jarvis.ears else 0
        voice_recency = math.exp(-(now - last_voice) / 300.0) if last_voice > 0 else 0
        energy_score = (voice_recency * 0.5) + (0.5 if idle_time < 300 else 0.1)
        
        # PROGRESS: goal velocity
        streak = jarvis.tasks.get_completion_streak() if jarvis.tasks else 0
        streak_factor = min(1.0, streak / 5.0)
        progress_score = (streak_factor * 0.7) + (0.3 if idle_time < 60 else 0)
        
        # STABILITY: consistency of the above
        stability_score = 1.0 - (switch_freq * 1.2)
        
        # 4. MOMENTUM
        momentum_score = (streak_factor * 0.6) + (voice_recency * 0.4)
        
        # 5. STATE OBJECT
        current_state = CognitiveState(
            focus=_clamp(focus_score),
            energy=_clamp(energy_score),
            progress=_clamp(progress_score),
            stability=_clamp(stability_score),
            momentum=_clamp(momentum_score),
            active_app=active_app,
            idle_time=idle_time,
            switch_rate=switch_freq,
            user_present=self._check_presence()
        )
        
        # 6. SALIENCY DETECTION (v8 Feature)
        if self._last_vector:
            diff = abs(current_state.focus - self._last_vector.focus) + \
                   abs(current_state.energy - self._last_vector.energy) + \
                   abs(current_state.progress - self._last_vector.progress)
            current_state.saliency = _clamp(diff)
        
        self._last_vector = current_state
        return current_state

    def _detect_active_app(self) -> str:
        # Placeholder/Wrapper for system app detection
        return "VSCode"

    def _check_presence(self) -> bool:
        from senses.camera import camera
        if not camera or not camera.enabled:
            return True
        return camera.is_user_present()

    def update_interaction(self):
        self._last_interaction = time.time()

def _clamp(val: float) -> float:
    return max(0.0, min(1.0, val))

# Singleton
state_compressor = StateCompressor()
