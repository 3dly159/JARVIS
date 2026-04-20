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
import random
from typing import Dict, List, Any, Optional, Callable, Tuple, Set
from datetime import datetime
from enum import IntEnum
from dataclasses import dataclass, field

logger = logging.getLogger("jarvis.cognition")

class Priority(IntEnum):
    EMERGENCY = 1      # Critical (System alert, Security)
    ACTIONABLE = 2     # Direct (Task stall, deadline)
    INFORMATIONAL = 3  # Indirect (User idle, habits)

TRIGGER_REGISTRY = {
    # 1. EMERGENCY (Immediate Bypass)
    "system_overheat":      {"priority": Priority.EMERGENCY, "base_attention": 1.0, "cooldown": 30},
    "resource_exhaustion":  {"priority": Priority.EMERGENCY, "base_attention": 1.0, "cooldown": 60},
    "security_alert":       {"priority": Priority.EMERGENCY, "base_attention": 1.0, "cooldown": 0},
    "task_crash":           {"priority": Priority.EMERGENCY, "base_attention": 1.0, "cooldown": 10},
    "execution_failure":    {"priority": Priority.EMERGENCY, "base_attention": 0.9, "cooldown": 10},

    # 2. ACTIONABLE (Productivity & Flow)
    "task_stall":           {"priority": Priority.ACTIONABLE, "base_attention": 0.7, "cooldown": 600},
    "task_overdue":         {"priority": Priority.ACTIONABLE, "base_attention": 0.8, "cooldown": 900},
    "focus_drop":           {"priority": Priority.ACTIONABLE, "base_attention": 0.6, "cooldown": 300},
    "long_session":         {"priority": Priority.ACTIONABLE, "base_attention": 0.5, "cooldown": 1800},
    "voice_interruption":   {"priority": Priority.ACTIONABLE, "base_attention": 0.9, "cooldown": 5},
    "repeat_request":       {"priority": Priority.ACTIONABLE, "base_attention": 0.7, "cooldown": 10},
    "hardware_throttling":  {"priority": Priority.ACTIONABLE, "base_attention": 0.6, "cooldown": 900},

    # 3. INFORMATIONAL (Habits & Context)
    "user_return":          {"priority": Priority.INFORMATIONAL, "base_attention": 0.5, "cooldown": 300},
    "user_idle":            {"priority": Priority.INFORMATIONAL, "base_attention": 0.3, "cooldown": 900},
    "session_start":        {"priority": Priority.INFORMATIONAL, "base_attention": 0.4, "cooldown": 0},
    "task_completed":       {"priority": Priority.INFORMATIONAL, "base_attention": 0.5, "cooldown": 0},

    # 4. POSITIVE (Focus Protection)
    "momentum_detected":    {"priority": Priority.INFORMATIONAL, "base_attention": 0.2, "cooldown": 600},
    "deep_focus":           {"priority": Priority.INFORMATIONAL, "base_attention": 0.1, "cooldown": 1200},
    "recovery_state":       {"priority": Priority.INFORMATIONAL, "base_attention": 0.6, "cooldown": 300},

    # 5. COMPOUND (Strategic Inferencing)
    "flow_state":           {"priority": Priority.INFORMATIONAL, "base_attention": 0.0, "cooldown": 0}, 
    "stuck_state":          {"priority": Priority.ACTIONABLE, "base_attention": 0.9, "cooldown": 900},
    "burnout_risk":         {"priority": Priority.ACTIONABLE, "base_attention": 0.8, "cooldown": 3600},
    "distraction_state":    {"priority": Priority.ACTIONABLE, "base_attention": 0.7, "cooldown": 600},
    "overwhelm_state":      {"priority": Priority.ACTIONABLE, "base_attention": 1.0, "cooldown": 1200},
    "frustration_state":    {"priority": Priority.ACTIONABLE, "base_attention": 1.0, "cooldown": 600},
}

@dataclass
class CognitiveState:
    """Unified Cognitive State Vector (Kernel v4/v8)"""
    # 4 Core Continuous Variables (0.0 to 1.0)
    focus: float = 0.5      # task clarity + low switching + engagement
    energy: float = 0.5     # user activity + context persistence
    progress: float = 0.5   # task velocity + completion ratio
    stability: float = 0.5  # low interruption + consistent usage

    # Contextual metadata
    user_present: bool = True
    active_app: str = "Unknown"
    idle_time: float = 0.0
    switch_rate: float = 0.0
    momentum_score: float = 0.0
    
    # Active labeled states (backwards compatibility for UI/Triage)
    active_states: Set[str] = field(default_factory=set)
    state_durations: Dict[str, float] = field(default_factory=dict)

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
        
        # ---------------- FLOW DOMINANCE (v1/v8) ----------------
        # Based on continuous focus and stability
        if state.focus > 0.8 and state.stability > 0.7:
            policy.suppress_low_priority = True
            policy.threshold_scale = 1.5
            policy.focus_protection = True
            policy.allow_interruptions = False
            policy.tone_modifier = "concise"

        # ---------------- OVERWHELM (v1/v8) ----------------
        # Low stability + high switch rate
        if state.switch_rate > 0.7 and state.energy > 0.8:
            policy.suppress_low_priority = True
            policy.threshold_scale = 0.8
            policy.tone_modifier = "calm_supportive"

        # ---------------- FRUSTRATION (v1/v8) ----------------
        # Low progress + consistent usage
        if state.progress < 0.3 and state.energy > 0.6:
            policy.threshold_scale = 0.5
            policy.tone_modifier = "helpful_direct"
            policy.allow_interruptions = True

        # ---------------- STUCK (v1/v8) ----------------
        # Low progress + high idle
        if state.progress < 0.2 and state.idle_time > 300:
            policy.allow_interruptions = True
            policy.tone_modifier = "guiding"

        # ---------------- MOMENTUM BOOST (v1/v8) ----------------
        if state.momentum_score > 0.7:
            policy.threshold_scale += 0.2

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
        self.state_builder = StateBuilder()
        self.resolver = PolicyResolver()
        self.filter = TriggerFilter()
        
        # Kernel Engines
        self.intentions = intent_engine
        self.plans = planning_engine
        self.world = world_model
        self.meta = meta_control
        
        # Cognitive Hardware
        self.attention_scores: Dict[str, float] = {}
        self.trigger_queue: List[Dict[str, Any]] = []
        self.active_policy = CognitivePolicy()
        
        # State Management
        self._active_states: Set[str] = set()
        self._state_durations: Dict[str, float] = {}
        self._fired_thresholds: Set[str] = set()
        self._last_trigger_time: Dict[str, float] = {}
        self._last_action_time = 0
        
        # Tuning
        self.attention_decay = 0.85
        self.soft_threshold = 0.6
        self.confidence_threshold = 0.7
        self._processing = False
        self._previous_idle_time = 0.0

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

    def trigger(self, trigger_name: str, data: Any = None):
        """
        Gathers attention for a specific trigger. 
        If attention crosses thresholds, the trigger is queued for evaluation.
        """
        now = time.time()
        if trigger_name not in TRIGGER_REGISTRY:
            logger.warning(f"Unknown trigger: {trigger_name}")
            return

        definition = TRIGGER_REGISTRY[trigger_name]
        
        # 0. Cooldown Enforcement (Per Trigger)
        last_t = self._last_trigger_time.get(trigger_name, 0)
        if now - last_t < definition["cooldown"]:
            return

        # 1. Accumulate Attention (Weighted & Capped)
        weight = self.priority_weights.get(trigger_name, 1.0)
        base_inc = definition["base_attention"] * weight
        
        current = self.attention_scores.get(trigger_name, 0.0)
        # Cap aggregation to prevent runaway importance
        new_score = min(2.0, current + base_inc) 
        self.attention_scores[trigger_name] = new_score
        
        logger.debug(f"Event: {trigger_name} (Attention: {new_score:.2f})")

        # 2. Threshold Check
        is_emergency = definition["priority"] == Priority.EMERGENCY
        if is_emergency or new_score >= self.soft_threshold:
            logger.info(f"Cognitive Trigger Crossed: {trigger_name} (Attention: {new_score:.2f})")
            self._queue_trigger(trigger_name, data, is_emergency)
            self._last_trigger_time[trigger_name] = now

    def _queue_trigger(self, name: str, data: Any, force: bool = False):
        """Adds a trigger to the batch queue with TTL."""
        # Deduplicate: If trigger of same name in queue, update data
        for item in self.trigger_queue:
            if item["name"] == name:
                item["data"] = data
                item["timestamp"] = time.time()
                return

        self.trigger_queue.append({
            "name": name,
            "data": data,
            "timestamp": time.time(),
            "force": force
        })
        
        # Process queue if not already busy
        self._process_queue_async()

    def _process_queue_async(self):
        from core.jarvis import jarvis
        if jarvis.loop and not jarvis.loop.is_closed():
             asyncio.run_coroutine_threadsafe(self._process_queue(), jarvis.loop)

    async def _process_queue(self):
        """Main batch processor for cognitions. Loops until empty."""
        if self._processing or not self.trigger_queue:
            return

        self._processing = True
        try:
            while self.trigger_queue:
                # 1. Clear expired triggers (TTL: 30s)
                now = time.time()
                self.trigger_queue = [t for t in self.trigger_queue if now - t["timestamp"] < 30]

                if not self.trigger_queue:
                    break

                # 2. Pick highest priority trigger
                self.trigger_queue.sort(key=lambda x: TRIGGER_REGISTRY[x["name"]]["priority"])
                top_trigger = self.trigger_queue.pop(0)

                # 3. Enter core cognition step
                success = await self._cognition_step(top_trigger["name"], top_trigger["data"])
                
                # 4. Attention Reset/Decay
                if success:
                    self.attention_scores[top_trigger["name"]] = 0.0
                else:
                    # If we evaluated but decided not to act, decay so we don't spam eval
                    self.attention_scores[top_trigger["name"]] *= 0.3

        finally:
            self._processing = False

    def _decay_attention(self):
        """Exponential decay of attention scores."""
        now = time.time()
        delta = now - self._last_decay_time
        if delta < 1: return
        
        # multiplier = decay ^ (delta / interval) 
        # interval = 10s for the 0.85 factor
        multiplier = self.attention_decay ** (delta / 10.0)
        
        for name in list(self.attention_scores.keys()):
            self.attention_scores[name] *= multiplier
            if self.attention_scores[name] < 0.05:
                del self.attention_scores[name]
        
        # 2. Drift adaptive weights back to baseline (clamped)
        # We drift towards 1.0 (baseline) by 1% per decay cycle
        for name in list(self.priority_weights.keys()):
            current = self.priority_weights[name]
            # Drift
            target = 1.0
            new_weight = current + (target - current) * 0.01
            # Clamp between 0.2 and 1.5
            self.priority_weights[name] = max(0.2, min(1.5, new_weight))

        self._last_decay_time = now

    def _loop(self):
        """Unified Executive Loop (v8)"""
        iteration = 0
        last_decay = time.time()
        
        while self._running:
            try:
                now = time.time()
                
                # 1. PERCEIVE & COMPRESS (Sensory -> CSV)
                state = self.state_builder.build()
                self.intentions.update(state)
                self.world.update(state)
                
                # 2. INTERPRET (Policy Resolution)
                self.active_policy = self.resolver.resolve(state)
                
                # 3. META-CONTROL (Kernel Self-Management)
                self.meta.evaluate_efficiency(state, self.active_policy)
                
                # 4. INTERRUPT BUDGET RECOVERY (v8)
                self.active_policy.interrupt_budget = min(1.0, self.active_policy.interrupt_budget + 0.1)
                
                # 5. DECAY ATTENTION
                delta = now - last_decay
                if delta >= 1:
                    multiplier = self.attention_decay ** (delta / 10.0)
                    for name in list(self.attention_scores.keys()):
                        self.attention_scores[name] *= multiplier
                    last_decay = now

                # 6. CONTINUOUS CHECKS
                self._check_time_triggers(state)
                self._check_compound_triggers(state)

                # 7. HEARTBEAT
                iteration += 1
                if iteration % 6 == 0:
                    logger.info(f"Cognitive Heartbeat: Focus={state.focus:.2f}, Intent={self.intentions.get_summary()}, {self.meta.get_summary()}")

            except Exception as e:
                logger.error(f"Kernel loop maintenance error: {e}")
            
            time.sleep(10)

    def _check_curiosity(self, state: dict):
        """Low-frequency autonomous trigger for exploration."""
        if state["idle_time"] > 180 and state["focus_level"] == "low" and "curiosity" not in self._fired_thresholds:
            self.trigger("curiosity")
            self._fired_thresholds.add("curiosity")

    def _check_compound_triggers(self, state: dict):
        """Derives high-level states from raw sensory signals with resolution logic."""
        now = time.time()
        
        # 1. Distraction State (Hysteresis)
        switch_freq = state.get("app_switch_frequency", 0)
        is_stagnant = state.get("task_velocity") == "stagnant"
        distraction_conf = min(1.0, switch_freq + (0.3 if is_stagnant else 0))
        
        if distraction_conf > 0.7 and "distraction_state" not in self._active_states:
            logger.info("Cognition: Entering DISTRACTION state.")
            self._active_states.add("distraction_state")
            self._state_durations["distraction_state"] = now
            self.trigger("distraction_state", {"confidence": distraction_conf})
        elif distraction_conf < 0.4 and "distraction_state" in self._active_states:
            logger.info("Cognition: Exiting DISTRACTION state.")
            self._active_states.remove("distraction_state")
            
        # 2. Flow State (Positive Partnering)
        if switch_freq < 0.2 and state.get("task_velocity") == "productive":
            if "flow_state" not in self._active_states:
                logger.info("Cognition: FLOW detected. Protecting focus.")
                self._active_states.add("flow_state")
                self._state_durations["flow_state"] = now
                self.trigger("flow_state")
        elif switch_freq > 0.4:
            if "flow_state" in self._active_states:
                logger.info("Cognition: FLOW broken.")
                self._active_states.discard("flow_state")

        # 3. Frustration Detection (Semantic + Signal)
        if is_stagnant and switch_freq > 0.6:
             if "frustration_state" not in self._active_states:
                 logger.warning("Cognition: High FRUSTRATION detected.")
                 self._active_states.add("frustration_state")
                 self._state_durations["frustration_state"] = now
                 self.trigger("frustration_state")

        # 4. Stuck State
        idle_time = state.get("idle_time", 0)
        if is_stagnant and idle_time > 300 and "stuck_state" not in self._active_states:
             logger.info("Cognition: USER STUCK detected.")
             self._active_states.add("stuck_state")
             self._state_durations["stuck_state"] = now
             self.trigger("stuck_state")
        elif (not is_stagnant or idle_time < 60) and "stuck_state" in self._active_states:
             self._active_states.remove("stuck_state")

        # Cleanup durations
        for s in list(self._state_durations.keys()):
            if s not in self._active_states:
                del self._state_durations[s]

    def _check_time_triggers(self, state: dict):
        """R reliably detects crossings of time thresholds and returns."""
        from core.jarvis import jarvis
        idle_time = state.get("idle_time", 0)
        
        # User Return Detection (Transition Detection)
        if self._previous_idle_time > 300 and idle_time < 5:
             self.trigger("user_return")
             # Reset thresholds so they can fire again next time user goes idle
             self._fired_thresholds.discard("user_idle_2m")
             self._fired_thresholds.discard("user_idle_5m")

        # Threshold-crossing Idle Checks (Exactly once per event)
        if idle_time > 120 and "user_idle_2m" not in self._fired_thresholds:
             self.trigger("user_idle", {"seconds": 120})
             self._fired_thresholds.add("user_idle_2m")
             
        if idle_time > 300 and "user_idle_5m" not in self._fired_thresholds:
             self._fired_thresholds.add("user_idle_5m")

        # Task Monitor Integration
        if jarvis.tasks:
            active = jarvis.tasks.list_active()
            for t in active:
                if t.is_stalled(stall_minutes=15):
                    self.trigger("task_stall", {"task_id": t.id})
                if t.is_overdue():
                    self.trigger("task_overdue", {"task_id": t.id})
        
        self._previous_idle_time = idle_time

    async def _cognition_step(self, trigger_name: str, data: Any) -> bool:
        """Unified Thinking Cycle (Perceive -> Interpret -> Decide -> Act)"""
        try:
            from core.jarvis import jarvis
            definition = TRIGGER_REGISTRY[trigger_name]
            priority = definition["priority"]
            is_emergency = priority == Priority.EMERGENCY

            # 1. PERCEIVE (Fresh Snapshot)
            state = self.state_builder.build()
            
            # 2. INTERPRET (Policy check)
            policy = self.resolver.resolve(state)
            
            # 3. FILTER (The Gate)
            if not self.filter.should_pass(trigger_name, state, policy):
                logger.debug(f"Action suppressed: Filtered by Policy (Trigger: {trigger_name})")
                return False

            # 4. PRESENCE & INHIBITION Gate
            if not state.user_present and not is_emergency:
                return False

            importance = self.attention_scores.get(trigger_name, 0.5)
            scaled_soft = self.soft_threshold * policy.threshold_scale
            
            if not is_emergency and importance < scaled_soft:
                logger.debug(f"Action inhibited: Importance ({importance:.2f}) < Scaled Threshold ({scaled_soft:.2f})")
                return False

            # 5. DECIDE (Deep Brain)
            logger.info(f"Cognitive evaluation started: {trigger_name}")
            decision = await jarvis.brain.proactive_decide(state, trigger_name)
            
            # 6. ACT
            if decision.get("act"):
                # Check confidence for non-emergency
                conf = decision.get("confidence", 0)
                if not is_emergency and conf < self.confidence_threshold:
                    return False
                
                # 7. CONSUME INTERRUPT BUDGET (v8)
                budget_cost = 0.3 # Default for medium value
                if priority == Priority.INFORMATIONAL: budget_cost = 0.1
                if priority == Priority.ACTIONABLE: budget_cost = 0.5
                if is_emergency: budget_cost = 0.0 # Free
                
                self.active_policy.interrupt_budget -= budget_cost
                
                self._execute(decision, trigger_name)
                self._last_action_time = time.time()
                return True
            
            return False

        except Exception as e:
            logger.error(f"Cognition step failed: {e}")
            return False

    def _calculate_interrupt_cost(self, state: dict) -> float:
        """
        Calculates the 'social cost' of interrupting the user.
        Formula: (Focus * Factor) + (Speech * Penalty) + (Recency * Exp-Decay)
        """
        from core.jarvis import jarvis
        
        # 1. Focus Penalty
        focus_map = {"high": 0.8, "med": 0.5, "low": 0.2}
        focus_level = focus_map.get(state.get("focus_level"), 0.2)
        cost = focus_level * 1.0  # weight 1.0
        
        # 2. Voice Penalty (Don't talk over yourself or user)
        if jarvis.voice and jarvis.voice.is_speaking:
            cost += 0.9
            
        # 3. Recency Penalty (Logarithmic/Exp decay)
        # We don't want to nag too frequently
        time_since = time.time() - self._last_action_time
        tau = 300.0 # 5 minute time constant
        recency_penalty = 1.0 * math.exp(-time_since / tau)
        cost += recency_penalty
        
        return cost

    def _is_meaningful(self, trigger: str, state: dict) -> bool:
        """
        Heuristics to filter out noise BEFORE calling the LLM.
        Implements 'Stagnation Escape' and 'Focus Suppression'.
        """
        # Focus Suppression: Respect the 'Zone'
        if state.get("focus_level") == "high":
            # Stagnation Escape: If idle too long in focus mode, maybe stuck?
            if state["idle_time"] > 300: # 5 minutes
                logger.info("Focus mode override: User may be stuck (idle > 300s).")
                return True
            
            # Otherwise, stay quiet
            if trigger != "system_alert":
                logger.debug(f"Suppressed trigger '{trigger}' due to High Focus.")
                return False

        # Deduplication / Throttling
        # (Already handled by trigger cooldowns and attention scores)
        
        return True

    async def _delayed_reflect(self, decision: dict, initial_state: dict, trigger: str, action_time: float):
        """
        Analyze the outcome after a delay.
        Updates adaptive weights based on engagement signals.
        """
        await asyncio.sleep(60)
        from core.jarvis import jarvis
        
        # 1. Capture user response time
        last_interact = jarvis.ears.get_last_interaction_time()
        user_reacted = last_interact > action_time
        latency = (last_interact - action_time) if user_reacted else 60.0
        
        end_state = self.state_builder.build()
        
        engagement = {
            "responded_vocal": user_reacted,
            "task_updated": end_state["task_velocity"] == "productive" and initial_state["task_velocity"] == "stagnant",
            "app_switched": end_state["user_activity"] != initial_state["user_activity"],
            "latency": latency
        }
        
        # 2. Determine Outcome
        is_engaged = any([engagement["responded_vocal"], engagement["task_updated"], engagement["app_switched"]])
        
        result_str = "Engaged" if is_engaged else "Ignored"
        logger.info(f"Reflection for '{trigger}': {result_str} (Latency: {engagement['latency']:.1f}s)")

        # 3. Update Adaptive Weights
        # Normal Penalty: Ignore -> Decrease weight (-0.2)
        # Flow Penalty: If we interrupted during Flow and were ignored -> HEAVY penalty (-0.5)
        current_weight = self.priority_weights.get(trigger, 1.0)
        
        is_flow = "flow_state" in initial_state.get("active_states", [])
        
        if is_engaged:
            new_weight = current_weight + 0.1
        else:
            penalty = -0.5 if is_flow else -0.2
            new_weight = current_weight + penalty
        
        self.priority_weights[trigger] = max(0.2, min(1.5, new_weight))

        # 4. Deep Brain Reflection (for long-term memory)
        reflection_context = {
            "trigger": trigger,
            "initial_state": initial_state,
            "decision": decision,
            "engagement": engagement,
            "outcome": result_str
        }
        
        reflection = await jarvis.brain.reflect(decision, f"Outcome: {result_str}. Details: {engagement}")
        jarvis.memory.log(f"Self-Reflection [{trigger}]: {result_str}. {reflection[:100]}...", category="cognition")

    def _execute(self, decision: dict, trigger_name: str):
        """Execute the chosen proactive action."""
        from core.jarvis import jarvis
        message = decision.get("message")
        if message:
            logger.info(f"Proactive action taken: {message[:60]}...")
            jarvis.say(message)
        
        # Could also trigger tools or agents here
        action_type = decision.get("action")
        if action_type == "check_tasks":
             jarvis.tasks.ping()


class StateBuilder:
    """Aggregates sensor data into a structured CognitiveState vector."""

    def __init__(self):
        self._start_time = time.time()
        self._last_interaction = time.time()
        self._app_history: List[str] = []
        self._max_history = 15
        self._momentum: float = 0.5

    def build(self) -> CognitiveState:
        from core.jarvis import jarvis
        now_ts = time.time()
        
        # 1. Raw Perception
        idle_time = now_ts - self._last_interaction
        active_app = self._detect_active_app()
        self._app_history.append(active_app)
        if len(self._app_history) > self._max_history:
             self._app_history.pop(0)

        switches = sum(1 for i in range(1, len(self._app_history)) if self._app_history[i] != self._app_history[i-1])
        switch_freq = switches / len(self._app_history) if len(self._app_history) > 1 else 0
        
        # 2. State Compression (Kernel v8 Math)
        # focus = clarity (context) - noise (switching)
        app_focus_weight = 1.0 if any(word in active_app for word in ["Code", "Terminal", "Doc"]) else 0.4
        focus_score = app_focus_weight * (1.0 - switch_freq)
        
        # energy = interaction intensity + context recency
        last_voice = jarvis.ears.get_last_interaction_time() if jarvis.ears else 0
        voice_recency = math.exp(-(now_ts - last_voice) / 300.0) if last_voice > 0 else 0
        energy_score = (voice_recency * 0.4) + (0.6 if idle_time < 300 else 0.1)

        # progress = completion streak + velocity
        streak = jarvis.tasks.get_completion_streak() if jarvis.tasks else 0
        streak_factor = min(1.0, streak / 5.0)
        progress_score = (streak_factor * 0.7) + (0.3 if idle_time < 60 else 0)

        # stability = focus consistency
        stability_score = 1.0 - (switch_freq * 1.2)
        
        # 3. Momentum
        momentum = (streak_factor * 0.6) + (voice_recency * 0.4)
        
        # 4. Construct Final State
        state = CognitiveState(
            focus=max(0.0, min(1.0, focus_score)),
            energy=max(0.0, min(1.0, energy_score)),
            progress=max(0.0, min(1.0, progress_score)),
            stability=max(0.0, min(1.0, stability_score)),
            user_present=self._check_presence(),
            active_app=active_app,
            idle_time=idle_time,
            switch_rate=switch_freq,
            momentum_score=momentum,
            active_states=set(cognition._active_states),
            state_durations=dict(cognition._state_durations)
        )
        
        return state

    def _detect_active_app(self) -> str:
        # Placeholder for real X11/Process tracking
        return "VSCode"

    def _check_presence(self) -> bool:
        from senses.camera import camera
        if not camera or not camera.enabled:
            return True
        return camera.is_user_present()

    def update_interaction(self):
        self._last_interaction = time.time()

class TriggerFilter:
    """Hard gate for suppression/amplification based on policy."""

    def should_pass(self, trigger: str, state: CognitiveState, policy: CognitivePolicy) -> bool:
        definition = TRIGGER_REGISTRY[trigger]
        priority = definition["priority"]

        # 1. EMERGENCY ALWAYS PASSES
        if priority == Priority.EMERGENCY:
            return True

        # 2. FLOW PROTECTION (v8)
        if policy.focus_protection and state.focus > 0.8:
            # Only allow Actionable or higher if importance is extreme
            if priority == Priority.INFORMATIONAL:
                return False
            
        # 3. INTERRUPT BUDGET (v8)
        if policy.interrupt_budget <= 0.0 and priority != Priority.EMERGENCY:
            return False

        # 4. GENERAL SUPPRESSION
        if not policy.allow_interruptions and priority != Priority.EMERGENCY:
            return False

        return True


# Singleton
cognition = CognitiveKernel()
