"""
run_suite.py - Execution Entry Point for Cognition Harness v8
"""
import sys
from pathlib import Path
import asyncio
import logging

# Ensure project root is in path
root = Path(__file__).resolve().parents[2]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from tests.harness.cognition_harness import CognitionHarness
from tests.harness.scenario_builder import (
    flow_state_scenario, stuck_scenario, emergency_scenario, chaos_scenario,
    stuck_interrupted_scenario
)
from tests.harness.metrics import CognitiveMetrics
from core.cognition import cognition
from core.state_compressor import state_compressor

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("jarvis.harness.suite")

async def main():
    logger.info("Initializing Cognition Test Harness v8 Suite...")
    
    harness = CognitionHarness(cognition, state_compressor)
    metrics = CognitiveMetrics()
    
    scenarios = {
        "Flow Protection": flow_state_scenario(),
        "Stuck Recovery": stuck_scenario(),
        "Emergency Override": emergency_scenario(),
        "Interrupted Recovery": stuck_interrupted_scenario(),
        "Chaos Stress Test": chaos_scenario()
    }
    
    final_report = {}
    
    for name, scenario in scenarios.items():
        logger.info(f"\n>>> Running Scenario: {name}")
        timeline = await harness.run_scenario(scenario)
        
        # In a real v8 system, emergency signals come from signals, not just CSV
        if name == "Emergency Override":
            # Manually inject the emergency signal into the last step
            last_tick = timeline[-1]
            if "overheat" in last_tick.sensory_input.get("system_alert", ""):
                 res = await harness.step({"system_alert": "overheat", "active_app": "VSCode"})
                 timeline.append(res)

        score_res = metrics.evaluate_suite(timeline)
        final_report[name] = score_res
        
        # Summary log for this scenario
        avg_focus = sum([t.state_vector.focus for t in timeline]) / len(timeline)
        logger.info(f"--- {name} Complete (Avg Focus: {avg_focus:.2f}) ---")

    # ------------------------------------------------------------------
    # FINAL REPORT PRINTING
    # ------------------------------------------------------------------
    print("\n" + "="*60)
    print(" JARVIS COGNITION HEALTH REPORT (v8 Pure Vector)")
    print("="*60)
    
    for scenario, scores in final_report.items():
        print(f"\n[Scenario: {scenario}]")
        for m, val in scores.items():
            color = "PASS" if val > 0.8 else "FAIL"
            print(f"  - {m:25}: {val:>10.2f} [{color}]")
            
    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(main())
