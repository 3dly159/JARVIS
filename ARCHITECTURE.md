# J.A.R.V.I.S. Architecture
## Just A Rather Very Intelligent System

**Status:** Design phase  
**Last updated:** 2026-04-16  
**Language:** Python  
**LLM:** Ollama + Mistral 7B (mistral:7b-instruct-q4_K_M)  
**Machine:** 24GB DDR5 RAM, RTX 3050 Laptop 6GB VRAM  

---

## Project Structure

```
JARVIS/
├── core/
│   ├── brain.py              # LLM interface (Ollama + Mistral 7B)
│   ├── memory.py             # Daily files + Memory Palace
│   ├── task_tracker.py       # Task queue, self-ping, progress
│   └── agent_manager.py      # Spawn/kill/monitor agents (20 max, 5 parallel)
│
├── senses/
│   ├── ears.py               # Whisper STT (local)
│   ├── voice.py              # Edge TTS
│   ├── eyes.py               # Live screen capture (mss)
│   ├── camera.py             # On-demand camera (OpenCV)
│   └── wake.py               # Wake word + hotkey listener
│
├── actions/
│   ├── executor.py           # Shell commands, file ops
│   ├── keyboard_mouse.py     # PyAutoGUI control
│   ├── app_control.py        # Open/close/focus applications
│   └── confirm.py            # Approval gate for dangerous actions
│
├── tools/
│   ├── registry.py           # Tool loader — brain picks tools from here
│   ├── web_search.py         # Web search
│   ├── file_browser.py       # Read/write/search filesystem
│   ├── calendar.py           # Calendar integration (future)
│   └── browser_control.py    # Browser automation (Playwright)
│
├── notifications/
│   ├── notifier.py           # Dispatch alerts (tray, voice, sound)
│   ├── tray.py               # System tray icon + popups
│   └── sounds.py             # Audio alerts
│
├── skills/
│   └── (auto-loaded skill modules)
│
├── system/
│   ├── monitor.py            # System health (psutil — CPU/RAM/VRAM)
│   ├── self_repair.py        # Issue detection + fix attempts
│   └── startup.py            # Autostart, background service, tray init
│
├── self_mod/
│   ├── code_editor.py        # JARVIS edits own codebase
│   └── sandbox.py            # Test changes before applying
│
├── ui/
│   ├── server.py             # FastAPI backend (localhost:8080)
│   ├── static/
│   │   ├── index.html
│   │   ├── app.js
│   │   └── style.css
│   └── routes/
│       ├── chat.py           # Chat + streaming
│       ├── sessions.py       # Session management
│       ├── settings.py       # Config editor
│       ├── agents.py         # Agent status + control
│       ├── tasks.py          # Task tracker
│       ├── memory.py         # Memory browser
│       └── system.py         # System health panel
│
├── sessions/                 # Persisted conversation sessions
├── memory/                   # Daily logs + Memory Palace
│   └── palace/
├── logs/                     # Debug + error logs
├── config.yaml               # All settings
├── requirements.txt
└── main.py                   # Entry point
```

---

## Module Responsibilities

### `core/brain.py`
- Wraps Ollama API
- Sends prompts, receives streamed responses
- Tool-calling logic (brain decides which tool to invoke)
- System prompt management (JARVIS personality + context injection)
- Model config: temperature, context window, etc.

### `core/memory.py`
- **Daily files:** `memory/YYYY-MM-DD.md` — raw log of the day
- **Memory Palace:** `memory/palace/` — important items, tagged and searchable
- Read/write/search interface for all other modules
- Periodic summarization (compress old daily files)
- Memory promotion (detect when something should move to Palace)

### `core/task_tracker.py`
- Task data model: id, title, status, steps, created, deadline, last_pinged
- Task queue with priority
- Self-ping: JARVIS checks its own tasks periodically, resumes stalled ones
- Progress logging per task
- Hooks into notifications for alerts

### `core/agent_manager.py`
- Agent pool: max 20 agents, max 5 running in parallel
- Agent lifecycle: spawn, assign task, monitor, kill
- Each agent is a thread/process with its own brain context
- Inter-agent messaging
- Agent types: researcher, executor, monitor, writer, etc.

### `senses/ears.py`
- Local Whisper (faster-whisper recommended)
- Continuous listen mode or push-to-talk
- Returns transcribed text to brain

### `senses/voice.py`
- Edge TTS wrapper
- Speaks text as audio
- Voice profile config (voice name, speed, pitch)
- Queue-based (non-blocking)

### `senses/eyes.py`
- Live screen capture via `mss`
- Configurable capture rate (don't burn CPU)
- Smart triggers: capture on change, not constantly
- Sends frames to brain as context when relevant

### `senses/camera.py`
- OpenCV on-demand capture
- JARVIS requests camera only when needed
- Single frame or short clip

### `senses/wake.py`
- Wake word detection ("Hey JARVIS") via Whisper or porcupine
- Hotkey combo (configurable, default: Ctrl+Space)
- Triggers active listening mode

### `actions/executor.py`
- Run shell commands safely
- File create/read/update/delete
- Always logs what it did

### `actions/keyboard_mouse.py`
- PyAutoGUI wrapper
- Type text, click, drag, scroll
- Screenshot-guided actions (works with eyes.py)

### `actions/confirm.py`
- Approval gate for dangerous/irreversible actions
- Config: which action types require confirmation
- Can confirm via voice, UI popup, or hotkey

### `tools/registry.py`
- Auto-discovers tools in `tools/`
- Exposes tool list + schemas to brain
- Brain picks tools via function-calling style prompting

### `notifications/notifier.py`
- Central dispatch: routes alerts to tray, voice, sound
- Priority levels: info, warning, urgent
- Do-not-disturb mode (respects quiet hours)

### `system/monitor.py`
- CPU, RAM, VRAM usage via psutil + pynvml
- JARVIS process health
- Alerts brain when resources are critical

### `system/self_repair.py`
- Detects crashes, hung agents, failed tasks
- Attempts automatic recovery
- Escalates to user if repair fails

### `self_mod/code_editor.py`
- JARVIS reads its own source files
- Writes/patches code based on brain instructions
- Validates syntax before saving

### `self_mod/sandbox.py`
- Runs new/modified code in isolation
- Reports success/failure back to code_editor
- Rollback support: keeps last-known-good copy

---

## Build Order

| # | Module | Why first |
|---|--------|-----------|
| 1 | `core/brain.py` | Everything else calls this |
| 2 | `core/memory.py` | JARVIS needs to remember from session 1 |
| 3 | `core/task_tracker.py` | Core autonomy — self-ping starts here |
| 4 | `core/agent_manager.py` | Multi-agent capability |
| 5 | `senses/ears.py` + `voice.py` | Talk and listen |
| 6 | `senses/wake.py` | Wake word / hotkey summon |
| 7 | `actions/` | JARVIS can now DO things |
| 8 | `tools/` | JARVIS can now KNOW things |
| 9 | `notifications/` | JARVIS can alert you |
| 10 | `senses/eyes.py` + `camera.py` | JARVIS can SEE |
| 11 | `ui/` | Control panel |
| 12 | `system/` | Self-monitoring |
| 13 | `self_mod/` | Self-modification (last — touches everything) |

---

## Key Design Principles

1. **Privacy first** — everything local, no cloud APIs required
2. **Modular** — each module works independently, wired together in `main.py`
3. **Fail safe** — dangerous actions require confirmation, changes are sandboxed
4. **Self-aware** — JARVIS knows what it can do (senses, tools, actions)
5. **Persistent** — memory and sessions survive restarts
6. **Observable** — all actions logged, UI shows everything live

---

## Dependencies (planned)

```
ollama
faster-whisper
edge-tts
mss
opencv-python
pyautogui
psutil
pynvml
fastapi
uvicorn
websockets
pyyaml
playwright
```
