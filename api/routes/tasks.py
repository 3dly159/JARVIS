"""ui/routes/tasks.py - Task tracker view and control"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("")
async def list_tasks():
    from core.jarvis import jarvis
    if not jarvis.tasks:
        return []
    return [t.to_dict() for t in jarvis.tasks.list_all()]


@router.get("/active")
async def active_tasks():
    from core.jarvis import jarvis
    if not jarvis.tasks:
        return []
    return [t.to_dict() for t in jarvis.tasks.list_active()]


@router.post("")
async def create_task(body: dict):
    from core.jarvis import jarvis
    if not jarvis.tasks:
        return JSONResponse({"error": "Task tracker not initialized"}, status_code=500)
    task = jarvis.tasks.create(
        title=body.get("title", "New Task"),
        description=body.get("description", ""),
        steps=body.get("steps", []),
        priority=body.get("priority", 5),
        deadline=body.get("deadline"),
    )
    return task.to_dict()


@router.get("/{task_id}")
async def get_task(task_id: str):
    from core.jarvis import jarvis
    if not jarvis.tasks:
        return JSONResponse({"error": "Not initialized"}, status_code=500)
    task = jarvis.tasks.get(task_id)
    if not task:
        return JSONResponse({"error": "Task not found"}, status_code=404)
    return task.to_dict()


@router.post("/{task_id}/complete")
async def complete_task(task_id: str, body: dict = {}):
    from core.jarvis import jarvis
    if jarvis.tasks:
        jarvis.tasks.complete(task_id, result=body.get("result", ""))
    return {"completed": task_id}


@router.delete("/{task_id}")
async def cancel_task(task_id: str):
    from core.jarvis import jarvis
    if jarvis.tasks:
        jarvis.tasks.cancel(task_id)
    return {"cancelled": task_id}


@router.get("/status/summary")
async def tasks_summary():
    from core.jarvis import jarvis
    if not jarvis.tasks:
        return {"summary": "Task tracker not initialized"}
    return {"summary": jarvis.tasks.summary(), "status": jarvis.tasks.status()}
