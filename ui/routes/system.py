"""ui/routes/system.py - System health panel"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
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
