import sys
import os
import asyncio
import logging

# Add project root to path
sys.path.append(os.getcwd())

# Minimal logging
logging.basicConfig(level=logging.INFO)

async def debug_cognition():
    print("--- JARVIS Cognition Debugger ---")
    
    # Import core components (will initialize them)
    from core.jarvis import jarvis
    from core.cognition import cognition
    
    # Initialize necessary components manually for the test
    # (Memory, Brain, etc. usually start in jarvis.initialize)
    print("Initializing Brain...")
    from core.brain import brain
    jarvis.brain = brain
    
    print("\n1. Testing State Builder...")
    state = cognition.state_builder.build()
    print(f"Current State: {state}")
    
    print("\n2. Testing Proactive Decision (Mock Event: user_idle)...")
    # We call the internal step directly to bypass cooldown/coordination
    print("Evaluating decision...")
    decision = await jarvis.brain.proactive_decide(state, "user_idle")
    print(f"Decision: {decision}")
    
    if decision.get("act"):
        print(f"SUCCESS: JARVIS wants to act: '{decision.get('message')}'")
    else:
        print("INFO: JARVIS decided NOT to act in this state.")

if __name__ == "__main__":
    asyncio.run(debug_cognition())
