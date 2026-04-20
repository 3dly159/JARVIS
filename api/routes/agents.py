"""ui/routes/agents.py - Agent status and control"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/")
async def list_agents():
    from core.jarvis import jarvis
    if not jarvis.agents:
        return []
    return [a.to_dict() for a in jarvis.agents.list_all()]


@router.get("/status")
async def agents_status():
    from core.jarvis import jarvis
    if not jarvis.agents:
        return {"error": "Agent manager not initialized"}
    return jarvis.agents.status()


@router.post("/spawn")
async def spawn_agent(body: dict):
    from core.jarvis import jarvis
    from core.agent_manager import AgentType, llm_work
    if not jarvis.agents:
        return JSONResponse({"error": "Agent manager not initialized"}, status_code=500)
    agent = await jarvis.agents.spawn(
        name=body.get("name", "agent"),
        task=body.get("task", ""),
        agent_type=AgentType(body.get("type", "general")),
        work_fn=llm_work(body.get("task", "")),
    )
    if agent:
        return agent.to_dict()
    return JSONResponse({"error": "Could not spawn agent (pool full?)"}, status_code=503)


@router.delete("/{agent_id}")
async def kill_agent(agent_id: str):
    from core.jarvis import jarvis
    if jarvis.agents:
        jarvis.agents.kill(agent_id)
    return {"killed": agent_id}


@router.get("/{agent_id}/log")
async def agent_log(agent_id: str):
    from core.jarvis import jarvis
    if not jarvis.agents:
        return []
    agent = jarvis.agents.get(agent_id)
    if not agent:
        return JSONResponse({"error": "Agent not found"}, status_code=404)
    return agent.log
