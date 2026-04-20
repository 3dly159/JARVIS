# J.A.R.V.I.S.
### Just A Rather Very Intelligent System

> *"At your service, sir."*

A fully local, privacy-first personal AI assistant. JARVIS can speak, listen, see your screen, control your computer, manage tasks autonomously, run multiple agents in parallel, and modify its own code — all running on your hardware with no cloud dependency.

---

## Features

| Capability | Details |
|-----------|---------|
| 🧠 **Brain** | NVIDIA NIM Cascaded Stack (Nano, Super, Ultra, Safety) |
| 🧠 **Cognition** | Kernel v8: 5-layer autonomous stack with predictive simulation |
| 🧠 **Memory** | Daily logs + Memory Palace (long-term tagged storage) |
| 🗣️ **Voice** | Microsoft Edge TTS — British male (en-GB-RyanNeural) |
| 👂 **Ears** | Local Whisper STT via faster-whisper (CUDA-accelerated) |
| 🔔 **Wake** | OpenWakeWord ("Hey JARVIS") + configurable hotkey |
| 👁️ **Eyes** | Live screen capture with smart change detection |
| 🕹️ **Executive** | Managed Interrupt Budget + Strategic Goal/Intention layers |
| ⚡ **Actions** | Shell commands, file ops, keyboard/mouse, app control |
| 🔧 **Tools** | Web search, file browser, browser automation (Playwright) |
| 🤖 **Agents** | Up to 20 agents, 5 running in parallel, auto-queued |
| 📋 **Tasks** | Autonomous task tracking with planning & decomposition |
| 🔄 **Self-mod** | JARVIS reads and edits its own codebase (sandboxed + backed up) |
| 🖥️ **UI** | Web dashboard at localhost:8090 (chat, tasks, agents, memory, settings) |
| ⚙️ **Config** | Hot-reloading config — change settings live without restart |
| 🛡️ **Privacy** | Encrypted NIM API + Local sensors — nothing stored in cloud |

---

## Quick Start

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/download) installed and running
- NVIDIA GPU recommended (RTX 3050+ with 6GB VRAM or better)

### Install

```bash
git clone https://github.com/3dly159/JARVIS.git
cd JARVIS
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

### First-time setup

```bash
python setup.py
```

The setup wizard will:
- Check all dependencies
- Pull the Mistral model via Ollama
- Detect your GPU
- Configure voice, wake word, hotkey, and UI port
- Write `config.yaml`

### Run

```bash
# Full UI mode (opens browser at http://localhost:8090)
python main.py

# Terminal/CLI mode (no UI)
python main.py --cli
```

---

## Project Structure

```
JARVIS/
├── main.py                   # Entry point
├── setup.py                  # First-run wizard
├── config.yaml               # All settings (hot-reloaded)
├── requirements.txt
│
├── AGENTS.md                 # Session startup navigation hub
├── SOUL.md                   # JARVIS personality & values
├── IDENTITY.md               # Canonical identity reference
├── USER.md                   # User profile (updated by JARVIS)
│
├── core/
│   ├── jarvis.py             # Central orchestrator
│   ├── brain.py              # Intelligence Engine (NIM Cascade)
│   ├── cognition.py          # Cognitive Kernel v8
│   ├── intentions.py         # Intention Engine
│   ├── goal_manager.py       # Persistent Goal System
│   ├── planning.py           # Planning Engine
│   ├── world_model.py        # World Model (Simulation)
│   ├── meta_control.py       # Meta-Control (Stabilization)
│   ├── memory.py             # Daily logs + Memory Palace
│   ├── context_loader.py     # Prompt assembly
│   ├── task_tracker.py       # Task management
│   ├── agent_manager.py      # Multi-agent pool
│   └── config_manager.py     # Hot-reload config
│
├── senses/
│   ├── voice.py              # Edge TTS
│   ├── ears.py               # Whisper STT
│   ├── wake.py               # OpenWakeWord + hotkey
│   ├── eyes.py               # Screen capture
│   └── camera.py             # On-demand camera
│
├── actions/
│   ├── executor.py           # Shell + file operations
│   ├── keyboard_mouse.py     # PyAutoGUI control
│   ├── app_control.py        # Window/app management
│   └── confirm.py            # Confirmation gate
│
├── tools/
│   ├── registry.py           # Tool registry
│   ├── web_search.py         # DuckDuckGo search
│   ├── file_browser.py       # Filesystem browser
│   └── browser_control.py    # Playwright automation
│
├── notifications/
│   ├── notifier.py           # Alert dispatcher
│   └── sounds.py             # Audio tones
│
├── system/
│   ├── monitor.py            # CPU/RAM/VRAM monitoring
│   ├── self_repair.py        # Auto-recovery
│   └── startup.py            # Autostart management
│
├── self_mod/
│   ├── code_editor.py        # Self-modification engine
│   └── sandbox.py            # Isolated code testing
│
├── ui/
│   ├── server.py             # FastAPI backend
│   ├── routes/               # API endpoints
│   └── static/               # Dashboard (HTML/CSS/JS)
│
├── memory/
│   ├── YYYY-MM-DD.md         # Daily logs
│   ├── tasks/                # Task persistence
│   └── palace/               # Memory Palace items
└── logs/
```

---

## Configuration

All settings live in `config.yaml`. Edit directly or use the Settings panel in the UI — changes apply **live** without restart.

Key settings:

```yaml
nvidia:
  tiers:
    nano:    "nvidia/nemotron-nano-8b-v1"
    super:   "nvidia/nemotron-super-49b-v1.5"
    ultra:   "nvidia/nemotron-ultra-253b-v1"
    safety:  "llama-3.1-nemoguard-8b-content-safety"
  temperature: 0.7

ui:
  port: 8090

agents:
  max_agents: 20
  max_parallel: 5
```

---

## Identity System

JARVIS loads its personality from files at every session start:

| File | Purpose |
|------|---------|
| `AGENTS.md` | Navigation hub — lists all files to load |
| `IDENTITY.md` | Canonical identity (name, tone, voice) |
| `SOUL.md` | Personality, values, how JARVIS speaks |
| `USER.md` | User profile — updated by JARVIS over time |

To add new instructions: create a `.md` file, add it to `AGENTS.md`, and JARVIS picks it up automatically next session.

---

## Testing Individual Modules

```bash
python core/brain.py         # Chat with JARVIS (LLM only)
python core/memory.py        # Test memory system
python senses/voice.py       # Hear JARVIS speak
python senses/ears.py        # Test Whisper STT
python senses/wake.py        # Test wake word / hotkey
python senses/eyes.py        # Test screen capture
python senses/camera.py      # Test camera
```

---

## Hardware Recommendations

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 16GB | 24GB+ |
| GPU VRAM | 4GB | 6GB+ (RTX 3050+) |
| Storage | 10GB free | 20GB+ |
| OS | Windows 10 / Ubuntu 20.04 | Ubuntu 22.04+ |

---

## Roadmap

- [x] Skills system (auto-loading skill modules)
- [ ] Calendar & email integration
- [ ] Multi-monitor support
- [x] Voice confirmation for dangerous actions
- [x] JARVIS-initiated conversation (proactive executive mind)
- [ ] Real-time vision-driven UI navigation

---

## Privacy

Everything aligns with local-first principles:
- LLM: NVIDIA NIM (Encrypted API)
- STT: faster-whisper (local)
- TTS: Edge TTS (cloud synthesis)
- Wake word: OpenWakeWord (local, CPU)
- Search: DuckDuckGo (minimal tracking)
- No telemetry, no accounts, no persistent cloud storage

---

## License

MIT — do what you want, sir.
