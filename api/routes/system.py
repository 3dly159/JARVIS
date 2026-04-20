"""ui/routes/system.py - System health panel"""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def system_status():
    from core.jarvis import jarvis
    return jarvis.status()


@router.get("/stats")
async def system_stats():
    from system.monitor import monitor
    return monitor.get_stats()


@router.get("/summary")
async def system_summary():
    from system.monitor import monitor
    return {"summary": monitor.get_summary()}


@router.post("/repair")
async def run_repair():
    from system.self_repair import self_repair
    issues = self_repair.run_check()
    return {"issues_found": len(issues), "issues": issues}


@router.get("/notifications")
async def notification_history():
    from core.jarvis import jarvis
    if not jarvis.notifier:
        return []
    return jarvis.notifier.get_history()


@router.get("/autostart")
async def autostart_status():
    from system.startup import startup
    return startup.status()


@router.post("/autostart/enable")
async def enable_autostart():
    from system.startup import startup
    ok = startup.enable_autostart()
    return {"enabled": ok}


@router.post("/autostart/disable")
async def disable_autostart():
    from system.startup import startup
    ok = startup.disable_autostart()
    return {"disabled": ok}


@router.get("/processes")
async def get_processes(limit: int = 10):
    import psutil
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
        try:
            pinfo = proc.info
            # Filter out zero CPU unless it's a jarvis process
            if pinfo['cpu_percent'] > 0.1 or 'jarvis' in pinfo['name'].lower():
                processes.append({
                    "pid": pinfo['pid'],
                    "name": pinfo['name'],
                    "cpu": f"{pinfo['cpu_percent']:.1f}%",
                    "mem": f"{pinfo['memory_percent']:.1f}%",
                    "state": "success" if pinfo['status'] == 'running' else "info"
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    # Sort by CPU and limit
    processes.sort(key=lambda x: float(x['cpu'].replace('%', '')), reverse=True)
    return processes[:limit]


@router.get("/agents")
async def get_agents():
    from core.agent_manager import agent_manager
    return [a.to_dict() for a in agent_manager.list_all()]


@router.post("/agents")
async def spawn_agent(data: dict):
    from core.agent_manager import agent_manager, AgentType, autonomous_work
    name = data.get("name", "Sentinel")
    task = data.get("task", "")
    steps = data.get("steps", [])
    mission_type = data.get("type", "general")
    
    # Combine steps into directive
    full_directive = task
    if steps:
        steps_str = "\n".join(f"- {s}" for s in steps)
        full_directive = f"{task}\n\nCritical Steps:\n{steps_str}"
        
    a_type = AgentType.GENERAL
    try:
        a_type = AgentType(mission_type)
    except ValueError:
        pass
        
    agent = await agent_manager.spawn(
        name=name,
        task=full_directive,
        agent_type=a_type,
        work_fn=autonomous_work(full_directive)
    )
    
    if not agent:
        return {"error": "Pool full", "status": "failed"}, 400
        
    return {"id": agent.id, "status": "deployed"}


@router.delete("/agents/{agent_id}")
async def kill_agent(agent_id: str):
    from core.agent_manager import agent_manager
    agent_manager.kill(agent_id)
    return {"status": "terminated"}
