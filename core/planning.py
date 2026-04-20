"""
core/planning.py - JARVIS Planning Engine (Kernel v3)
Hierarchical task decomposition and dependency management.
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("jarvis.planning")

@dataclass
class PlanStep:
    id: int
    task: str
    status: str = "pending"
    dependencies: List[int] = field(default_factory=list)

@dataclass
class Plan:
    id: str
    goal_id: str
    steps: List[PlanStep] = field(default_factory=list)
    
class PlanningEngine:
    """
    Decomposes high-level goals into tactical steps.
    Used by agents and the brain for long-horizon success.
    """

    def __init__(self):
        self.active_plans: Dict[str, Plan] = {}

    async def generate_plan(self, goal_description: str) -> Plan:
        """Calls the brain to decompose a goal into steps."""
        from core.jarvis import jarvis
        
        prompt = f"""
Decompose this high-level goal into clear, tactical steps:
Goal: {goal_description}

Return a list of steps in a logical order.
"""
        # We use Super/Ultra for planning
        response = await jarvis.brain.think(prompt, tier="super")
        
        # Parse steps and create Plan object
        plan_id = f"plan_{len(self.active_plans) + 1}"
        plan = Plan(id=plan_id, goal_id=goal_description, steps=[])
        
        for i, line in enumerate(response.split('\n')):
            if line.strip():
                plan.steps.append(PlanStep(id=i, task=line.strip()))
        
        self.active_plans[plan_id] = plan
        logger.info(f"Generated new plan: {plan_id} with {len(plan.steps)} steps.")
        return plan

    def get_summary(self) -> str:
        if not self.active_plans:
            return "No active strategic plans."
        return f"Tracking {len(self.active_plans)} active plans."

# Singleton
planning_engine = PlanningEngine()
