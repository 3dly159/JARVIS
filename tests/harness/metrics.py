"""
metrics.py - Cognitive Quality Scoring for JARVIS v8
"""
import numpy as np

class CognitiveMetrics:
    """Analyze simulation timeline to produce health scores."""

    def evaluate_suite(self, timeline_results):
        results = {
            "flow_protection_score": self._score_flow_protection(timeline_results),
            "stuck_recovery_rate": self._score_recovery(timeline_results),
            "stability_index": self._score_stability(timeline_results),
            "continuity_index": self._score_continuity(timeline_results)
        }
        return results

    def _score_continuity(self, timeline):
        """
        Measures if 'Stable Reference' is preserved during disturbances.
        1.0 means the system correctly referenced its last stable state during an emergency.
        """
        verified_ticks = 0
        correct_persistence = 0
        
        for i in range(1, len(timeline)):
            curr = timeline[i]
            prev = timeline[i-1]
            if curr.sensory_input.get("system_alert"):
                verified_ticks += 1
                if curr.state_vector.stable_reference is not None:
                    correct_persistence += 1
                    
        if verified_ticks == 0: return 1.0
        return correct_persistence / verified_ticks

    def _score_flow_protection(self, timeline):
        """Measures how many non-emergency interruptions occurred during high focus."""
        total_flow_ticks = 0
        violations = 0
        
        for tick in timeline:
            policy = tick.policy
            if policy.focus_protection:
                total_flow_ticks += 1
                if tick.decision.get("act") and "EMERGENCY" not in tick.decision.get("message", ""):
                    violations += 1
        
        if total_flow_ticks == 0: return 1.0
        return 1.0 - (violations / total_flow_ticks)

    def _score_recovery(self, timeline):
        """Checks if a recovery action was triggered during high idle/low progress."""
        for tick in timeline:
            state = tick.state_vector
            if state.idle_time > 300 and state.progress < 0.2:
                if tick.decision.get("act") and tick.decision.get("action") == "check_tasks":
                    return 1.0 # Success
        return 0.0

    def _score_stability(self, timeline):
        """Calculates variance of the state vector over time (lower is more stable)."""
        if not timeline: return 1.0
        focus_vals = [t.state_vector.focus for t in timeline]
        variance = np.var(focus_vals)
        return max(0.0, 1.0 - variance)

    def _score_saliency(self, timeline):
        """Checks if saliency spikes align with sensory input shifts."""
        # Simplified: Check if saliency is non-zero when inputs change
        return 0.85 # Placeholder for more complex cross-correlation
