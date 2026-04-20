import os
import re
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pathlib import Path

router = APIRouter()

LOG_FILE = Path(__file__).parent.parent.parent / "logs" / "jarvis.log"

def parse_log_line(line: str):
    """
    Parses a log line like:
    22:38:37 [INFO] jarvis.main: JARVIS online.
    """
    pattern = r"(\d{2}:\d{2}:\d{2}) \[(\w+)\] ([\w\.-]+): (.+)"
    match = re.match(pattern, line)
    if match:
        ts, level, source, message = match.groups()
        return {
            "ts": ts,
            "level": level.lower(),
            "source": source,
            "message": message
        }
    return None

@router.get("")
async def get_logs(limit: int = 100):
    """Read and return last N log lines."""
    if not LOG_FILE.exists():
        return JSONResponse({"error": "Log file not found"}, status_code=404)
    
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()[-limit:]
        
        parsed_logs = []
        for line in lines:
            parsed = parse_log_line(line.strip())
            if parsed:
                parsed_logs.append(parsed)
        
        return parsed_logs
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
