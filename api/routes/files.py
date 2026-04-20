"""api/routes/files.py - Generic file read/write access for HUD editors"""

import os
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
ROOT = Path(__file__).parent.parent.parent

# Allowed directories for editing
ALLOWED_PATHS = [
    ROOT / "SOUL.md",
    ROOT / "AGENTS.md",
    ROOT / "IDENTITY.md",
    ROOT / "USER.md",
    ROOT / "memory",
    ROOT / "sessions"
]

class FileUpdate(BaseModel):
    path: str
    content: str

def is_safe(path: Path) -> bool:
    """Check if the path is within allowed files or directories."""
    resolved = path.resolve()
    for allowed in ALLOWED_PATHS:
        allowed_res = allowed.resolve()
        if allowed_res.is_file() and resolved == allowed_res:
            return True
        if allowed_res.is_dir() and str(resolved).startswith(str(allowed_res)):
            return True
    return False

@router.get("/read")
async def read_file(path: str):
    """Read file content."""
    file_path = ROOT / path.lstrip("/")
    if not is_safe(file_path):
        raise HTTPException(status_code=403, detail="Access denied to this terminal sector.")
    
    if not file_path.exists():
         raise HTTPException(status_code=404, detail="File not found on disk.")
         
    try:
        return {"content": file_path.read_text(encoding="utf-8")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/write")
async def write_file(body: FileUpdate):
    """Write file content."""
    file_path = ROOT / body.path.lstrip("/")
    if not is_safe(file_path):
        raise HTTPException(status_code=403, detail="Access denied to this terminal sector.")
        
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(body.content, encoding="utf-8")
        return {"success": True, "path": body.path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
