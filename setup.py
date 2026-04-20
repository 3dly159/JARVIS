"""
setup.py - JARVIS Onboarding Wizard

Run this once before starting JARVIS for the first time.
Checks dependencies, configures settings, writes config.yaml.

Usage: python setup.py
"""

import os
import sys
import subprocess
import shutil
import yaml
from pathlib import Path

ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "config.yaml"

# ---------------------------------------------------------------------------
# Colours (terminal)
# ---------------------------------------------------------------------------

def c(text, code): return f"\033[{code}m{text}\033[0m"
def green(t): return c(t, "32")
def red(t):   return c(t, "31")
def yellow(t):return c(t, "33")
def bold(t):  return c(t, "1")
def cyan(t):  return c(t, "36")

def ok(msg):   print(f"  {green('✓')} {msg}")
def fail(msg): print(f"  {red('✗')} {msg}")
def warn(msg): print(f"  {yellow('!')} {msg}")
def info(msg): print(f"  {cyan('→')} {msg}")

def ask(prompt, default=""):
    val = input(f"  {bold(prompt)}" + (f" [{default}]" if default else "") + ": ").strip()
    return val if val else default

def ask_yn(prompt, default=True):
    suffix = " [Y/n]" if default else " [y/N]"
    val = input(f"  {bold(prompt)}{suffix}: ").strip().lower()
    if not val:
        return default
    return val in ("y", "yes")


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_python():
    print(bold("\n[1] Python version"))
    v = sys.version_info
    if v.major == 3 and v.minor >= 10:
        ok(f"Python {v.major}.{v.minor}.{v.micro}")
        return True
    else:
        fail(f"Python {v.major}.{v.minor} — JARVIS requires Python 3.10+")
        return False


def check_pip_packages():
    print(bold("\n[2] Python packages"))
    required = [
        ("ollama", "ollama"),
        ("faster_whisper", "faster-whisper"),
        ("edge_tts", "edge-tts"),
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("yaml", "pyyaml"),
        ("psutil", "psutil"),
        ("mss", "mss"),
        ("cv2", "opencv-python"),
        ("pyautogui", "pyautogui"),
        ("openwakeword", "openwakeword"),
        ("watchdog", "watchdog"),
    ]
    missing = []
    for import_name, pkg_name in required:
        try:
            __import__(import_name)
            ok(pkg_name)
        except ImportError:
            fail(f"{pkg_name} — not installed")
            missing.append(pkg_name)

    if missing:
        print()
        if ask_yn(f"Install {len(missing)} missing package(s) now?", default=True):
            print()
            subprocess.run(
                [sys.executable, "-m", "pip", "install"] + missing,
                check=False
            )
        else:
            warn("Some packages missing. Run: pip install -r requirements.txt")
    return True


def check_ollama():
    print(bold("\n[3] Ollama"))
    if shutil.which("ollama"):
        ok("ollama CLI found")
    else:
        fail("ollama not found in PATH")
        info("Install from: https://ollama.com/download")
        info("Then run: ollama serve")
        return False, None

    # Check if running
    import requests
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        r.raise_for_status()
        models = [m["name"] for m in r.json().get("models", [])]
        ok(f"Ollama running. Models: {models if models else 'none pulled yet'}")
        return True, models
    except Exception:
        fail("Ollama not running. Start it with: ollama serve")
        return False, []


def check_model(available_models: list):
    print(bold("\n[4] LLM Model"))
    recommended = "gemma4:latest"

    if any(recommended in m for m in available_models):
        ok(f"{recommended} already pulled")
        return recommended

    warn(f"{recommended} not found")
    if ask_yn(f"Pull {recommended} now? (~4GB download)", default=True):
        print()
        result = subprocess.run(["ollama", "pull", recommended])
        if result.returncode == 0:
            ok(f"{recommended} pulled successfully")
            return recommended
        else:
            fail("Pull failed. Try manually: ollama pull " + recommended)

    # Let user pick alternative
    alt = ask("Enter model name to use instead", default=recommended)
    return alt


def check_gpu():
    print(bold("\n[5] GPU / VRAM"))
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        name = pynvml.nvmlDeviceGetName(handle)
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        vram_gb = mem.total / 1024**3
        ok(f"{name} — {vram_gb:.1f}GB VRAM")
        device = "cuda"
    except Exception:
        warn("No NVIDIA GPU detected — Whisper will use CPU (slower)")
        device = "cpu"
    return device


def check_microphone():
    print(bold("\n[6] Microphone"))
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        count = p.get_device_count()
        mics = []
        for i in range(count):
            info = p.get_device_info_by_index(i)
            if info.get("maxInputChannels", 0) > 0:
                mics.append(f"[{i}] {info['name']}")
        p.terminate()

        if mics:
            ok(f"Found {len(mics)} input device(s):")
            for m in mics[:5]:
                info(m)
        else:
            warn("No microphone found — voice input unavailable")
        return bool(mics)
    except Exception as e:
        warn(f"Microphone check failed: {e}")
        return False


# ---------------------------------------------------------------------------
# Configure
# ---------------------------------------------------------------------------

def configure(model: str, stt_device: str) -> dict:
    print(bold("\n[7] Configuration"))
    print()

    # TTS voice
    print("  Available voices (Edge TTS):")
    voices = [
        ("en-GB-RyanNeural",    "British Male  — closest to MCU JARVIS (recommended)"),
        ("en-US-GuyNeural",     "American Male"),
        ("en-GB-SoniaNeural",   "British Female"),
        ("en-US-JennyNeural",   "American Female"),
    ]
    for i, (v, desc) in enumerate(voices, 1):
        print(f"    {i}. {v} — {desc}")

    choice = ask("Select voice (1-4)", default="1")
    try:
        tts_voice = voices[int(choice) - 1][0]
    except Exception:
        tts_voice = "en-GB-RyanNeural"
    ok(f"Voice: {tts_voice}")

    # Whisper model
    print()
    print("  Whisper model sizes (accuracy vs speed):")
    whisper_models = [
        ("tiny.en",   "Fastest, least accurate"),
        ("base.en",   "Good balance (recommended)"),
        ("small.en",  "More accurate, slower"),
        ("medium.en", "Most accurate, needs more RAM"),
    ]
    for i, (m, desc) in enumerate(whisper_models, 1):
        print(f"    {i}. {m} — {desc}")

    wchoice = ask("Select Whisper model (1-4)", default="2")
    try:
        stt_model = whisper_models[int(wchoice) - 1][0]
    except Exception:
        stt_model = "base.en"
    ok(f"Whisper model: {stt_model}")

    # Wake word
    wake_word = ask("Wake word", default="hey jarvis")
    ok(f"Wake word: {wake_word}")

    # Hotkey
    hotkey = ask("Hotkey to summon JARVIS", default="ctrl+space")
    ok(f"Hotkey: {hotkey}")

    # UI port
    port = ask("Web UI port", default="8090")
    ok(f"UI port: {port}")

    # Build config
    cfg = {
        "llm": {
            "model": model,
            "ollama_host": "http://localhost:11434",
            "temperature": 0.7,
            "context_window": 163840,
        },
        "voice": {
            "tts_engine": "edge-tts",
            "tts_voice": tts_voice,
            "tts_rate": "+0%",
            "tts_pitch": "+0Hz",
            "stt_model": stt_model,
            "stt_device": stt_device,
            "wake_word": wake_word,
            "hotkey": hotkey,
        },
        "ui": {
            "host": "127.0.0.1",
            "port": int(port),
            "open_browser_on_start": True,
        },
        "agents": {"max_agents": 20, "max_parallel": 5},
        "memory": {
            "daily_log_dir": "memory/",
            "palace_dir": "memory/palace/",
            "summarize_after_days": 7,
        },
        "monitor": {
            "enabled": True,
            "check_interval_seconds": 30,
            "cpu_alert_threshold": 90,
            "ram_alert_threshold": 85,
            "vram_alert_threshold": 90,
        },
        "tasks": {
            "self_ping_interval_seconds": 60,
            "stall_threshold_minutes": 10,
        },
        "actions": {
            "require_confirmation": ["shell_command", "file_delete", "keyboard_mouse"],
            "confirmation_timeout_seconds": 30,
        },
        "self_mod": {
            "enabled": True,
            "sandbox_before_apply": True,
            "backup_on_modify": True,
        },
        "notifications": {
            "tray_enabled": True,
            "voice_alerts": True,
            "quiet_hours_start": "23:00",
            "quiet_hours_end": "08:00",
        },
        "logging": {
            "level": "INFO",
            "log_dir": "logs/",
            "log_conversations": True,
        },
    }
    return cfg


# ---------------------------------------------------------------------------
# Create directories
# ---------------------------------------------------------------------------

def create_dirs():
    print(bold("\n[8] Creating directories"))
    dirs = [
        ROOT / "memory",
        ROOT / "memory" / "palace",
        ROOT / "memory" / "tasks",
        ROOT / "logs",
        ROOT / "sessions",
        ROOT / "skills",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        ok(str(d.relative_to(ROOT)))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print()
    print(bold(cyan("=" * 55)))
    print(bold(cyan("   J.A.R.V.I.S. — Setup Wizard")))
    print(bold(cyan("   Just A Rather Very Intelligent System")))
    print(bold(cyan("=" * 55)))
    print()
    print("  This wizard will configure JARVIS for your machine.")
    print("  It only needs to run once.")
    print()

    ok_python = check_python()
    if not ok_python:
        sys.exit(1)

    check_pip_packages()

    ollama_ok, available_models = check_ollama()
    model = check_model(available_models) if ollama_ok else "gemma4:latest"
    stt_device = check_gpu()
    check_microphone()

    cfg = configure(model, stt_device)
    create_dirs()

    # Write config
    print(bold("\n[9] Writing config.yaml"))
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)
    ok(f"Config written to {CONFIG_PATH.name}")

    # Done
    print()
    print(bold(green("=" * 55)))
    print(bold(green("   Setup complete! JARVIS is ready.")))
    print(bold(green("=" * 55)))
    print()
    ui_url = f"http://127.0.0.1:{cfg['ui']['port']}"
    print(f"  Start JARVIS:     {bold('python main.py')}")
    print(f"  Terminal mode:    {bold('python main.py --cli')}")
    print(f"  Web UI:           {bold(ui_url)}")
    print()


if __name__ == "__main__":
    main()
