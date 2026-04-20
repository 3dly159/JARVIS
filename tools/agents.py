import asyncio
from core.agent_manager import agent_manager, AgentType, autonomous_work
from tools.registry import registry

@registry.register(
    name="spawn_agent",
    description="Delegate a complex or long-running task to a background autonomous agent.",
    params={
        "name": "str - A descriptive name for the agent.",
        "task": "str - The full directive for the agent to follow.",
        "mission_type": "str - Type of agent: general, researcher, executor, analyst."
    }
)
def spawn_agent(name: str, task: str, mission_type: str = "general") -> str:
    """
    Delegate a task to a background agent.
    """
    try:
        # Map mission_type string to AgentType enum
        a_type = AgentType.GENERAL
        if mission_type == "researcher": a_type = AgentType.RESEARCHER
        elif mission_type == "executor": a_type = AgentType.EXECUTOR
        elif mission_type == "analyst": a_type = AgentType.ANALYST
        
        # We need an async wrapper because spawn is now async.
        # We use the main loop captured by agent_manager
        loop = getattr(agent_manager, "loop", None)
        if not loop:
            # Fallback for direct calls if loop isn't captured yet
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                return "Error: Main event loop not found. Systems are likely still booting."
        
        # Session Context Capture
        from core.context import session_id_ctx
        session_id = session_id_ctx.get()

        coro = agent_manager.spawn(
            name=name,
            task=task,
            agent_type=a_type,
            work_fn=autonomous_work(task),
            session_id=session_id
        )
        
        # Schedule the task on the main loop
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        agent = future.result(timeout=5) # Wait for spawn (not completion)
        
        if agent:
            return f"Agent '{name}' (ID: {agent.id}) has been dispatched for task: {task}. I will notify you when the mission is complete, sir."
        return "Failed to spawn agent. Pool likely full."
        
    except Exception as e:
        return f"Error delegating task: {e}"
