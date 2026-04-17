"""ui/routes/memory.py - Memory browser (daily logs + Memory Palace)"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/today")
async def today_log():
    from core.jarvis import jarvis
    if not jarvis.memory:
        return {"content": ""}
    return {"content": jarvis.memory.today()}


@router.get("/log/{date}")
async def log_for_date(date: str):
    from core.jarvis import jarvis
    from datetime import date as dt
    if not jarvis.memory:
        return {"content": ""}
    try:
        log_date = dt.fromisoformat(date)
        return {"content": jarvis.memory.daily.read_date(log_date)}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.get("/dates")
async def available_dates():
    from core.jarvis import jarvis
    if not jarvis.memory:
        return []
    return jarvis.memory.daily.list_dates()


@router.get("/palace")
async def palace_list():
    from core.jarvis import jarvis
    if not jarvis.memory:
        return []
    return jarvis.memory.palace.list_all()


@router.get("/palace/search")
async def palace_search(q: str = ""):
    from core.jarvis import jarvis
    if not jarvis.memory or not q:
        return []
    return jarvis.memory.palace.search(q)


@router.post("/palace")
async def palace_store(body: dict):
    from core.jarvis import jarvis
    if not jarvis.memory:
        return JSONResponse({"error": "Memory not initialized"}, status_code=500)
    item_id = jarvis.memory.remember(
        content=body.get("content", ""),
        title=body.get("title", ""),
        tags=body.get("tags", []),
    )
    return {"id": item_id}


@router.delete("/palace/{item_id}")
async def palace_delete(item_id: str):
    from core.jarvis import jarvis
    if jarvis.memory:
        jarvis.memory.forget(item_id)
    return {"deleted": item_id}
