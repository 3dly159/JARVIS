from fastapi import APIRouter
from fastapi.responses import JSONResponse
from core.jarvis import jarvis

router = APIRouter()

@router.get("")
async def get_tools():
    """List all registered tools in the JARVIS registry."""
    try:
        from tools.registry import registry
        tools_list = registry.get_all()
        # Add category if missing in registry data for UI consistency
        for t in tools_list:
            if "category" not in t:
                t["category"] = "general"
        return tools_list
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
