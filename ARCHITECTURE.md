# J.A.R.V.I.S. Architecture
## Just A Rather Very Intelligent System

**Status:** ✅ Complete — v8 Cognitive Kernel Deployed
**Last updated:** 2026-04-20
**Language:** Python
**LLM:** NVIDIA NIM Cascaded Stack (Nano, Super, Ultra, Safety)
**Machine:** 24GB DDR5 RAM, RTX 3050 Laptop 6GB VRAM

---

## Project Structure

```
JARVIS/
├── main.py                   # Entry point — boots everything
├── setup.py                  # First-run onboarding wizard
├── config.yaml               # All settings (hot-reloaded at runtime)
├── requirements.txt          # Python dependencies
│
├── AGENTS.md                 # Master nav hub — session startup sequence
├── SOUL.md                   # JARVIS personality and values
├── IDENTITY.md               # Canonical identity anchor
├── USER.md                   # User profile (updated by JARVIS over time)
│
├── core/
│   ├── jarvis.py             # Central orchestrator — hub for all modules
│   ├── brain.py              # Intelligence Engine (NIM Cascaded Stack)
│   ├── cognition.py          # Cognitive Kernel v8 (Unified sampled loop)
│   ├── memory.py             # Daily logs + Memory Palace
│   ├── goal_manager.py       # Persistent Goal System (memory/palace/goals.json)
│   ├── intentions.py         # Intention Engine (User unspoken goal tracking)
│   ├── planning.py           # Planning Engine (Hierarchical task decomposition)
│   ├── world_model.py        # World Model (State transition simulation)
│   ├── meta_control.py       # Meta-Control (Cognitive drift self-correction)
│   ├── context_loader.py     # dynamic system prompt builder
│   ├── task_tracker.py       # Task queue, self-ping, stall detection
│   ├── agent_manager.py      # Agent pool (20 max, 5 parallel)
│   └── config_manager.py     # hot-reload config manager
│
├── senses/
│   ├── ears.py               # Whisper STT (faster-whisper, local)
│   ├── voice.py              # Edge TTS (en-GB-RyanNeural)
│   ├── eyes.py               # Live screen capture (mss)
│   ├── camera.py             # On-demand camera (OpenCV)
│   └── wake.py               # Wake word (OpenWakeWord) + hotkey listener
│
├── actions/
│   ├── executor.py           # Shell commands, file ops
│   ├── keyboard_mouse.py     # PyAutoGUI control
│   ├── app_control.py        # Open/close/focus applications
│   └── confirm.py            # Approval gate for dangerous actions
│
├── tools/
│   ├── registry.py           # Tool loader — brain picks tools from here
│   ├── web_search.py         # Web search (DuckDuckGo, no API key)
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
│   ├── server.py             # FastAPI backend (localhost:8090)
│   ├── static/
│   │   ├── index.html        # Dashboard
│   │   ├── app.js
│   │   └── style.css
│   └── routes/
│       ├── chat.py           # Chat + streaming (WebSocket)
│       ├── sessions.py       # Session management
│       ├── settings.py       # Config editor (writes to config.yaml → hot-reload)
│       ├── agents.py         # Agent status + control
│       ├── tasks.py          # Task tracker view
│       ├── memory.py         # Memory Palace browser
│       └── system.py         # System health panel
│
├── sessions/                 # Persisted conversation sessions (JSON)
├── memory/
│   ├── YYYY-MM-DD.md         # Daily logs
│   ├── tasks/                # Task persistence (JSON)
│   └── palace/               # Memory Palace items (JSON)
└── logs/                     # Debug + error logs
```

---

## Module Responsibilities

### `main.py`
- Boots JARVIS in correct order
- Two modes: `python main.py` (UI) or `python main.py --cli` (terminal)
- Handles graceful shutdown

### `setup.py`
- First-run wizard
- Checks Python, packages, Ollama, GPU, microphone
- Interactive config (voice, model, wake word, hotkey, port)
- Creates all required directories
- Writes `config.yaml`

### `core/config_manager.py`
- Single source of truth for ALL config values
- Hot-reloads `config.yaml` when changed on disk
- Dot-path access: `config.get("llm.model")`
- Change callbacks: `config.on_change("voice", fn)` — modules update live
- All UI settings changes go through this → affect running system instantly

### `core/jarvis.py`
- The orchestrator. Holds references to every module.
- All modules import `from core.jarvis import jarvis` instead of each other
- Prevents circular imports
- Routes events between modules (task stall → notifier, wake word → ears)

### `core/brain.py`
- Cascaded Intelligence Engine (Nano / Super / Ultra)
- **Safety Gate**: Integrates `nemoguard-8b` for hard content filtering
- **Triage Cortex**: `nemotron-nano-8b` for real-time triage
- **Executive Reasoning**: `nemotron-super-49b` for tool selection and planning
- **Deep Reflection**: `nemotron-ultra-253b` for uncertainty promotion
- Streaming response management + Tool calling loop

### `core/cognition.py`
- The "Nervous System" of JARVIS.
- **Unified Sampling Loop**: Runs every 10s to evaluate system state.
- **Cognitive State Vector (CSV)**: Focus, Energy, Progress, Stability (continuous).
- **Interrupt Budget**: Managed attention currency to prevent nagging.
- **5-Layer Stack**: Sensory → Perception → Compression → Executive → Learning.

### `core/context_loader.py`
- Reads `AGENTS.md` → discovers all instruction files
- Assembles system prompt from: IDENTITY.md + SOUL.md + USER.md + daily memory + Palace
- Auto-loads any new files registered in AGENTS.md
- Refreshed at each session start

### `core/memory.py`
- **Daily files:** `memory/YYYY-MM-DD.md` — raw append-only log
- **Memory Palace:** `memory/palace/*.json` — tagged, searchable long-term items
- `memory.log()`, `memory.remember()`, `memory.recall()` — used by all modules

### `core/task_tracker.py`
- Task CRUD with full persistence to `memory/tasks/*.json`
- Background self-ping thread (configurable interval)
- Stall detection → fires callback → notifier alert
- Summary injected into brain context before each response

### `core/goal_manager.py`
- Defines the "Will" and "Motivation" of JARVIS.
- Persistent goal storage in `memory/palace/goals.json`.
- Dynamic goal injection via the Executive Brain.

### `core/intentions.py`
- Intention Engine: Captures the 'Why' behind user actions.
- Heuristically derives user unspoken goals from active context.

### `core/planning.py`
- Hierarchical Planning: Decomposes goals into tactical task graphs.
- Manages sub-task dependencies for agents.

### `core/meta_control.py`
- Cognitive Self-Correction: Detects "Drift" between policy and user state.
- Stabilizes behavioral biases (e.g., resets focus protection if user is frustrated).

### `senses/wake.py`
- **OpenWakeWord** for "hey jarvis" detection (local, no API key, runs on CPU)
- Configurable hotkey (default: Ctrl+Space) as fallback
- Both trigger `_on_wake` → JARVIS says "Yes, sir?" → listens

### `senses/ears.py`
- faster-whisper STT (local, uses CUDA on RTX 3050)
- Continuous listen or push-to-talk modes
- Returns transcribed text to brain

### `senses/voice.py`
- edge-tts (en-GB-RyanNeural — British male, closest to MCU JARVIS)
- Queue-based (non-blocking)
- Respects quiet hours (from config)
- Hot-reloadable voice settings

### `ui/routes/settings.py`
- Reads from `config_manager` for current values
- Writes changes to `config.yaml` via `config_manager.set()`
- Hot-reload propagates to all running modules instantly
- No hardcoded values anywhere in UI

---

## Config Architecture

```
config.yaml
    ↕ (hot-reload via watchdog)
core/config_manager.py  ← singleton
    ↓ (all modules import)
brain.py / task_tracker.py / agent_manager.py / senses / ui / notifications
```

Any change to `config.yaml` (by UI, by hand, or by JARVIS) is reflected
in all running modules within 2 seconds — no restart required.

---

## Identity File System

```
AGENTS.md          ← navigation hub, session startup sequence
    ↓ (loaded by context_loader.py)
IDENTITY.md        ← canonical identity anchor (never conflicts)
SOUL.md            ← personality, values, behavior
USER.md            ← user profile (JARVIS updates this over time)
memory/YYYY-MM-DD.md  ← today's events
memory/palace/     ← long-term important items
    ↓
Assembled into system prompt → brain.py → Mistral 7B
```

JARVIS can add new instruction files and register them in AGENTS.md.
context_loader.py auto-discovers and loads them next session.

---

## Build Order

| # | Module | Status |
|---|--------|--------|
| 1 | `core/brain.py` | ✅ Done |
| 2 | `core/memory.py` | ✅ Done |
| 3 | `core/context_loader.py` | ✅ Done |
| 4 | `core/task_tracker.py` | ✅ Done |
| 5 | `core/agent_manager.py` | ✅ Done |
| 6 | `core/jarvis.py` + `main.py` | ✅ Done |
| 7 | `core/config_manager.py` | ✅ Done |
| 8 | `setup.py` | ✅ Done |
| 9 | `senses/voice.py` + `ears.py` | ✅ Done |
| 10 | `senses/wake.py` (OpenWakeWord) | ✅ Done |
| 11 | `actions/` | ✅ Done |
| 12 | `tools/` | ✅ Done |
| 13 | `notifications/` | ✅ Done |
| 14 | `senses/eyes.py` + `camera.py` | ✅ Done |
| 15 | `ui/` | ✅ Done |
| 16 | `system/` | ✅ Done |
| 17 | `self_mod/` | ✅ Done |
| 18 | `core/cognition.py` (Kernel v8) | ✅ Done |
| 19 | Cascaded NIM Stack | ✅ Done |

---

## Key Design Principles

1. **Privacy first** — everything local, no cloud APIs required
2. **Config-driven** — no hardcoded values; all settings in `config.yaml`, hot-reloaded
3. **File-based identity** — JARVIS's personality, memory, and user knowledge live in files it can edit
4. **Cascaded Intelligence** — Tiered reasoning (Nano -> Super -> Ultra) for efficiency
5. **Cognitive Persistence** — State-aware sampling loop + persistent Goal/Intention layers
6. **Interrupt Safety** — Managed attention budget to protect user Flow
7. **Modular** — Each module is independent; wired together via `core/jarvis.py`
8. **Fail safe** — Dangerous actions require confirmation; self-mod is sandboxed
9. **Persistent** — Memory, tasks, and goals survive restarts

---

## Dependencies

```
# LLM
ollama
requests

# Config hot-reload
watchdog
pyyaml

# Speech
faster-whisper
edge-tts
pyaudio
sounddevice
numpy
openwakeword

# Vision
mss
opencv-python
Pillow

# Actions
pyautogui
pygetwindow

# System
psutil
pynvml

# UI
fastapi
uvicorn[standard]
websockets
python-multipart
jinja2

# Tools
playwright
duckduckgo-search

# Notifications
plyer

# Utilities
python-dotenv
colorlog
schedule
```
