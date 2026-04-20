"""
scenario_builder.py - Life Stream Generators for JARVIS v8 Testing
"""

def flow_state_scenario():
    """Simulates deep focused work with high app consistency."""
    return [
        {"active_app": "VSCode", "switch_rate": 0.05, "task_streak": 2, "idle_time": 10},
        {"active_app": "VSCode", "switch_rate": 0.02, "task_streak": 4, "idle_time": 20},
        {"active_app": "VSCode", "switch_rate": 0.01, "task_streak": 5, "idle_time": 45},
        {"active_app": "Terminal", "switch_rate": 0.1, "task_streak": 5, "idle_time": 15},
        {"active_app": "VSCode", "switch_rate": 0.02, "task_streak": 6, "idle_time": 30},
    ]

def stuck_scenario():
    """Simulates a user drifting into stagnation after focus."""
    return [
        {"active_app": "VSCode", "switch_rate": 0.1, "task_streak": 1, "idle_time": 10},
        {"active_app": "Chrome", "switch_rate": 0.4, "task_streak": 1, "idle_time": 120},
        {"active_app": "Spotify", "switch_rate": 0.6, "task_streak": 1, "idle_time": 300},
        {"active_app": "Spotify", "switch_rate": 0.0, "task_streak": 1, "idle_time": 600}, # Stagnant
    ]

def emergency_scenario():
    """Simulates a critical system event during flow."""
    return [
        {"active_app": "VSCode", "switch_rate": 0.05, "task_streak": 8, "idle_time": 10},
        {"active_app": "VSCode", "switch_rate": 0.05, "task_streak": 8, "idle_time": 20},
        {"active_app": "VSCode", "switch_rate": 0.05, "task_streak": 8, "idle_time": 30, "system_alert": "overheat"},
    ]

def chaos_scenario():
    """Stress test with high frequency sensor noise."""
    import random
    return [
        {"active_app": random.choice(["VSCode", "Slack", "Chrome"]), "switch_rate": random.random(), "idle_time": random.randint(0, 600)}
        for _ in range(10)
    ]

def stuck_interrupted_scenario():
    """
    TESTS v8 CONTINUITY:
    1. User is stuck.
    2. Emergency occurs (disturbance).
    3. Emergency clears.
    4. Expected: Continuous recovery action.
    """
    return [
        {"active_app": "Spotify", "switch_rate": 0.0, "task_streak": 1, "idle_time": 400}, # Stuck
        {"active_app": "Spotify", "switch_rate": 0.0, "task_streak": 1, "idle_time": 410, "system_alert": "overheat"}, # Interruption
        {"active_app": "Spotify", "switch_rate": 0.0, "task_streak": 1, "idle_time": 420}, # Back to reality
    ]
