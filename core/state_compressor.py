"""
core/state_compressor.py - JARVIS State Compression Layer
Aggregates sensory input into a unified Cognitive State Vector (CSV).
"""

import time
import math
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any

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
    
    # Continuity (v8 Finalization)
    disturbance: float = 0.0   # Current level of interruption/emergency
    stable_reference: Optional['CognitiveState'] = None # The state before disturbance
    
    # Metadata
    active_app: str = "Unknown"
    idle_time: float = 0.0
    switch_rate: float = 0.0
    user_present: bool = True
    
    # Active states (for backwards compatibility/labels)
    active_labels: Set[str] = field(default_factory=set)

class CognitiveContinuity:
    """
    Handles temporal state persistence.
    Protects 'Stable Baselines' from being wiped by emergencies.
    """
    def __init__(self):
        self.stable_baseline: Optional[CognitiveState] = None
        self.disturbance_level = 0.0
        self.interruption_history: List[str] = []
        self._max_history = 10

    def trigger_disturbance(self, level: float, reason: str):
        self.disturbance_level = max(self.disturbance_level, level)
        self.interruption_history.append(reason)
        if len(self.interruption_history) > self._max_history:
            self.interruption_history.pop(0)
        logger.info(f"Continuity: Disturbance detected ({reason}) -> Level {level:.2f}")

    def update(self, current_vector: CognitiveState):
        """Reconciles the current vector with the stable baseline."""
        # Decay disturbance over time
        self.disturbance_level *= 0.8
        if self.disturbance_level < 0.05:
            self.disturbance_level = 0.0
            
        # Update stable baseline only if NOT disturbed
        if self.disturbance_level == 0.0:
            if not self.stable_baseline or current_vector.saliency < 0.3:
                 self.stable_baseline = current_vector
        
        current_vector.disturbance = self.disturbance_level
        current_vector.stable_reference = self.stable_baseline

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
        self.continuity = CognitiveContinuity()

    def compress(self, raw_input: Optional[Dict[str, Any]] = None) -> CognitiveState:
        """The core Perception -> Compression step."""
        from core.jarvis import jarvis
        now = time.time()
        
        # 1. RAW SENSORY INPUT
        if raw_input:
            idle_time = raw_input.get("idle_time", 0.0)
            active_app = raw_input.get("active_app", "Simulation")
            switch_freq = raw_input.get("switch_rate", 0.0)
            last_voice = now - raw_input.get("voice_recency_offset", 999)
            streak = raw_input.get("task_streak", 0)
            user_present = raw_input.get("user_present", True)
        else:
            idle_time = now - self._last_interaction
            active_app = self._detect_active_app()
            self._app_history.append(active_app)
            if len(self._app_history) > self._max_history:
                self._app_history.pop(0)

            # 2. SIGNAL PROCESSING
            switches = sum(1 for i in range(1, len(self._app_history)) if self._app_history[i] != self._app_history[i-1])
            switch_freq = switches / len(self._app_history) if len(self._app_history) > 1 else 0
            
            last_voice = jarvis.ears.get_last_interaction_time() if (jarvis and jarvis.ears) else 0
            streak = jarvis.tasks.get_completion_streak() if (jarvis and jarvis.tasks) else 0
            user_present = self._check_presence()

        # 3. VECTOR CALCULATION (v8 Logic)
        # FOCUS: app relevance + switching noise
        app_weight = 1.0 if any(w in active_app.lower() for w in ["code", "term", "doc", "web"]) else 0.4
        focus_score = app_weight * (1.0 - (switch_freq * 1.5))
        
        # ENERGY: interaction recency
        voice_recency = math.exp(-(now - last_voice) / 300.0) if last_voice > 0 else 0
        energy_score = (voice_recency * 0.5) + (0.5 if idle_time < 300 else 0.1)
        
        # PROGRESS: goal velocity
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
            user_present=user_present
        )
        
        # 6. SALIENCY DETECTION (v8 Feature)
        if self._last_vector:
            diff = abs(current_state.focus - self._last_vector.focus) + \
                   abs(current_state.energy - self._last_vector.energy) + \
                   abs(current_state.progress - self._last_vector.progress)
            current_state.saliency = _clamp(diff)
        
        # 7. CONTINUITY (v8 Finalization)
        if raw_input and "system_alert" in raw_input:
             self.continuity.trigger_disturbance(0.9, raw_input["system_alert"])
             
        self.continuity.update(current_state)
        
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
