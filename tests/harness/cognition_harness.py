import time
import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger("jarvis.harness")

@dataclass
class SimulationTick:
    timestamp: float
    sensory_input: Dict[str, Any]
    state_vector: Any
    saliency: float
    policy: Any
    decision: Dict[str, Any]

class MockBrain:
    """Deterministic Brain for simulation results."""
    async def proactive_decide(self, state, signals):
        # Deterministic logic for testing
        if any(s in ["security_alert", "system_overheat"] for s in signals):
            return {"act": True, "message": "EMERGENCY: SYSTEM CRITICAL", "tier": "mock"}
            
        if state.focus > 0.8 and "state_drift" in signals:
            return {"act": False, "message": "Protecting Flow.", "tier": "mock"}
            
        if state.progress < 0.2 and state.idle_time > 300:
            return {"act": True, "message": "You seem stuck, sir. Need a hand?", "action": "check_tasks", "tier": "mock"}
            
        return {"act": False, "message": "Stable condition.", "tier": "mock"}

class CognitionHarness:
    """
    Simulation runtime for J.A.R.V.I.S. Kernel v8.
    Allows replaying sensory streams and measuring cognitive drift.
    """

    def __init__(self, kernel, compressor):
        self.kernel = kernel
        self.compressor = compressor
        self.brain = MockBrain()
        self.timeline: List[SimulationTick] = []
        self._virtual_time = 0.0

    async def step(self, sensory_input: Dict[str, Any]):
        """Execute one virtual tick of cognition."""
        self._virtual_time += 10.0  # Default 10s steps
        
        # 1. Perception
        state = self.compressor.compress(sensory_input)
        
        # 2. Kernel Logic (Internal Policy & Triage)
        # Note: We manually trigger cognition steps because the real brain is async
        signals = []
        if state.saliency > self.kernel.saliency_threshold:
            signals.append("state_drift")
            
        # 3. Decision
        decision = await self.brain.proactive_decide(state, signals)
        
        # 4. Record
        tick = SimulationTick(
            timestamp=self._virtual_time,
            sensory_input=sensory_input,
            state_vector=state,
            saliency=state.saliency,
            policy=self.kernel.resolver.resolve(state),
            decision=decision
        )
        self.timeline.append(tick)
        return tick

    async def run_scenario(self, scenario: List[Dict[str, Any]]):
        """Execute a full list of sensory events."""
        self.timeline = []
        self._virtual_time = 0.0
        results = []
        for event in scenario:
            res = await self.step(event)
            results.append(res)
        return results
