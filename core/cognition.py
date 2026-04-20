"""
core/cognition.py - JARVIS Autonomous Cognition

This module implements the "Nervous System" and "Executive Control" of JARVIS.
It runs a background loop that gathers state, evaluates goals, and decides 
whether to take proactive actions.
"""

import logging
import threading
import time
import asyncio
import math
import logging
import threading
from enum import IntEnum
from typing import Dict, List, Any, Optional, Callable, Tuple, Set
from core.state_compressor import state_compressor, CognitiveState
from core.brain import brain

logger = logging.getLogger("jarvis.cognition")

class Priority(IntEnum):
    EMERGENCY = 1
    ACTIONABLE = 2
    INFORMATIONAL = 3

class CognitivePolicy:
    """Represents the resolved behavioral biases for the current state."""
    def __init__(self):
        self.suppress_low_priority = False
        self.threshold_scale = 1.0
        self.focus_protection = False
        self.allow_interruptions = True
        self.tone_modifier = "neutral"
        self.interrupt_budget = 1.0

class PolicyResolver:
    """Determines the effective cognitive policy (THE BRAIN OF THE SYSTEM)."""

    def resolve(self, state: CognitiveState) -> CognitivePolicy:
        policy = CognitivePolicy()
        
        # ---------------- FLOW DOMINANCE ----------------
        if state.focus > 0.8 and state.stability > 0.7:
            policy.suppress_low_priority = True
            policy.threshold_scale = 1.5
            policy.focus_protection = True
            policy.allow_interruptions = False
            policy.tone_modifier = "concise"

        # ---------------- OVERWHELM ----------------
        if state.switch_rate > 0.7 and state.energy > 0.8:
            policy.suppress_low_priority = True
            policy.threshold_scale = 0.8
            policy.tone_modifier = "calm_supportive"

        # ---------------- FRUSTRATION ----------------
        if state.progress < 0.3 and state.energy > 0.6:
            policy.threshold_scale = 0.5
            policy.tone_modifier = "helpful_direct"
            policy.allow_interruptions = True

        # ---------------- STUCK ----------------
        if state.focus > 0.5 and state.progress < 0.2 and state.idle_time > 300:
            policy.allow_interruptions = True
            policy.tone_modifier = "guiding"

        return policy

class CognitiveKernel:
    """
    JARVIS Cognitive Kernel (v8)
    Maintains a continuous sampling loop for executive decisions.
    
    5-Layer Stack:
    1. Sensory (Sensors -> raw data)
    2. Perception (StateBuilder -> CSV)
    3. State Compression (IntentEngine -> User Goal)
    4. Executive Brain (PolicyResolver + Cascaded Brain)
    5. Learning (MetaControl + Reflection)
    """

    def __init__(self):
        from core.intentions import intent_engine
        from core.planning import planning_engine
        from core.world_model import world_model
        from core.meta_control import meta_control
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.resolver = PolicyResolver()
        self.filter = TriggerFilter()
        
        # Kernel Engines
        self.intentions = intent_engine
        self.plans = planning_engine
        self.world = world_model
        self.meta = meta_control
        
        self.active_policy = CognitivePolicy()
        self._last_action_time = 0
        self._active_signals: List[str] = []
        
        # Tuning
        self.saliency_threshold = 0.4
        self._processing = False

    def start(self):
        """Start the cognition thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="cognition-loop")
        self._thread.start()
        logger.info("Cognition: Nervous system online (Loop starting).")

    def stop(self):
        self._running = False
        logger.info("Cognition loop stopping.")

    def signal(self, signal_name: str):
        """Asynchronous signal of an external event (e.g. system alert)."""
        if signal_name not in self._active_signals:
            self._active_signals.append(signal_name)
        
        # Immediate triage if signal is high priority
        if signal_name in ["security_alert", "system_overheat"]:
            self._process_immediate(signal_name)

    def _process_immediate(self, signal: str):
        from core.jarvis import jarvis
        if jarvis.loop:
            asyncio.run_coroutine_threadsafe(self._cognition_step([signal]), jarvis.loop)

    def _loop(self):
        """Unified Executive Loop (Pure v8 - State-Driven)"""
        while self._running:
            try:
                # 1. PERCEIVE & COMPRESS (Sensory -> CSV)
                state = state_compressor.compress()
                self.intentions.update(state)
                self.world.update(state)
                
                # 2. INTERPRET (Policy Resolution)
                self.active_policy = self.resolver.resolve(state)
                
                # 3. META-CONTROL
                self.meta.evaluate_efficiency(state, self.active_policy)
                self.active_policy.interrupt_budget = min(1.0, self.active_policy.interrupt_budget + 0.1)

                # 4. SALIENCY CHECK (Autonomous Decision)
                # We forward to the Brain if Saliency is high OR we have active signals
                if state.saliency > self.saliency_threshold or self._active_signals:
                    logger.debug(f"High Saliency detected ({state.saliency:.2f}). Forwarding to Executive Brain.")
                    self._process_immediate("state_drift")

                # 5. HEARTBEAT
                logger.info(f"Cognitive Heartbeat: CSV=[F:{state.focus:.1f} E:{state.energy:.1f} P:{state.progress:.1f} S:{state.stability:.1f}] "
                            f"Intent={self.intentions.get_summary()}")

            except Exception as e:
                logger.error(f"Kernel loop error: {e}")
            
            time.sleep(10)

    async def _cognition_step(self, signals: list[str]) -> bool:
        """Unified Thinking Cycle (Perceive -> Interpret -> Decide -> Act)"""
        try:
            from core.jarvis import jarvis
            
            # 1. PERCEIVE (Fresh Snapshot)
            state = state_compressor.compress()
            
            # 2. INTERPRET (Policy check)
            policy = self.resolver.resolve(state)
            
            # 3. FILTER (The Gate)
            if not self.filter.should_pass(signals, state, policy):
                return False

            # 4. DECIDE (Deep Brain)
            logger.info("Cognitive Forwarding: Sending State Vector to Executive Brain.")
            decision = await jarvis.brain.proactive_decide(state, signals)
            
            # Reset signals after forwarding
            self._active_signals = []

            # 5. ACT
            if decision.get("act"):
                self._execute(decision)
                self._last_action_time = time.time()
                return True
            
            return False

        except Exception as e:
            logger.error(f"Cognition step failed: {e}")
            return False

    def _execute(self, decision: dict):
        """Execute the chosen proactive action."""
        from core.jarvis import jarvis
        message = decision.get("message")
        if message:
            logger.info(f"Executive Decision: {message[:60]}...")
            jarvis.say(message)
        
        # Could also trigger tools or agents here
        action_type = decision.get("action")
        if action_type == "check_tasks":
             jarvis.tasks.ping()

class TriggerFilter:
    """Hard gate for suppression/amplification based on policy."""

    def should_pass(self, signals: list[str], state: CognitiveState, policy: CognitivePolicy) -> bool:
        # 1. EMERGENCY ALWAYS PASSES
        if any(s in ["security_alert", "system_overheat"] for s in signals):
            return True

        # 2. FLOW PROTECTION (v8)
        if policy.focus_protection and state.focus > 0.8:
            return False
            
        # 3. INTERRUPT BUDGET (v8)
        if policy.interrupt_budget <= 0.3:
            return False

        # 4. GENERAL SUPPRESSION
        if not policy.allow_interruptions:
            return False

        return True


# Singleton
cognition = CognitiveKernel()
