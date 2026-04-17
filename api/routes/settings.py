"""ui/routes/settings.py - Config editor (reads/writes config.yaml via config_manager)"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/")
async def get_settings():
    """Return all current settings."""
    from core.config_manager import config
    return config.all()


@router.get("/{section}")
async def get_section(section: str):
    """Return a specific config section."""
    from core.config_manager import config
    return config.section(section)


@router.post("/")
async def update_settings(body: dict):
    """
    Update one or more settings.
    Body: {"key": "llm.temperature", "value": 0.9}
    or:   {"updates": [{"key": "...", "value": "..."}, ...]}
    """
    from core.config_manager import config
    try:
        if "key" in body and "value" in body:
            config.set(body["key"], body["value"])
            return {"updated": body["key"], "value": body["value"]}
        elif "updates" in body:
            for item in body["updates"]:
                config.set(item["key"], item["value"])
            return {"updated": len(body["updates"]), "keys": [i["key"] for i in body["updates"]]}
        return JSONResponse({"error": "Provide 'key'+'value' or 'updates' list"}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/reload")
async def reload_settings():
    """Force reload config from disk."""
    from core.config_manager import config
    config.reload()
    return {"reloaded": True}
