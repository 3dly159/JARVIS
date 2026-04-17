"""ui/routes/skills.py - Skills management API"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/")
async def list_skills():
    from skills.loader import skill_loader
    return skill_loader.list_skills()


@router.get("/summary")
async def skills_summary():
    from skills.loader import skill_loader
    return {"summary": skill_loader.get_summary(), "status": skill_loader.status()}


@router.get("/search")
async def search_skills(q: str = ""):
    from skills.manager import skill_manager
    if not q:
        return {"results": "Provide a search query."}
    return {"results": skill_manager.search(q)}


@router.post("/install")
async def install_skill(body: dict):
    from skills.manager import skill_manager
    name = body.get("name", "").strip()
    version = body.get("version")
    if not name:
        return JSONResponse({"error": "Provide skill name"}, status_code=400)
    return skill_manager.install(name, version=version)


@router.post("/update")
async def update_skill(body: dict):
    from skills.manager import skill_manager
    name = body.get("name", "").strip()
    if name == "__all__":
        return skill_manager.update_all()
    if not name:
        return JSONResponse({"error": "Provide skill name or '__all__'"}, status_code=400)
    return skill_manager.update(name)


@router.delete("/{skill_name}")
async def remove_skill(skill_name: str):
    from skills.manager import skill_manager
    return skill_manager.remove(skill_name)


@router.post("/create")
async def create_skill(body: dict):
    from skills.manager import skill_manager
    return skill_manager.create_local(
        name=body.get("name", "").strip(),
        description=body.get("description", ""),
        with_python=body.get("with_python", False),
    )


@router.post("/reload")
async def reload_skills():
    from skills.loader import skill_loader
    skills = skill_loader.reload()
    return {"reloaded": len(skills), "skills": [s.name for s in skills]}
