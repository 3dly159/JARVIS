"""
main.py - JARVIS Entry Point

Boots the entire system in the correct order.
Run with: python main.py
"""

import logging
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging setup (must happen before any imports)
# ---------------------------------------------------------------------------

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE   = "%H:%M:%S"

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=LOG_DATE,
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

# File logging
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)
file_handler = logging.FileHandler(log_dir / "jarvis.log", encoding="utf-8")
file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE))
logging.getLogger().addHandler(file_handler)

logger = logging.getLogger("jarvis.main")

# ---------------------------------------------------------------------------
# Boot
# ---------------------------------------------------------------------------

async def boot():
    from core.jarvis import jarvis

    # 1. Initialize core modules
    jarvis.initialize()
    
    # 2. Initialize senses (non-fatal if unavailable)
    logger.info("Initializing senses...")
    jarvis.init_senses()

    # 3. Initialize notifications
    logger.info("Initializing notifications...")
    jarvis.init_notifications()

    # 4. Initialize UI
    logger.info("Initializing UI...")
    jarvis.init_ui()

    # 5. JARVIS announces itself (using async say if updated, but say is simple)
    jarvis.say("JARVIS online. Good to be back, sir.")
    logger.info("JARVIS boot complete.")

    return jarvis


# ---------------------------------------------------------------------------
# CLI mode (no UI)
# ---------------------------------------------------------------------------

async def run_cli(jarvis):
    """Simple terminal chat loop for testing without the full UI."""
    print("\n" + "=" * 50)
    print("  J.A.R.V.I.S. — Terminal Mode")
    print("  Type 'exit' to shut down.")
    print("=" * 50 + "\n")

    while True:
        try:
            import aioconsole
            user_input = await aioconsole.ainput("You: ")
            user_input = user_input.strip()
        except (KeyboardInterrupt, EOFError):
            break
        except ImportError:
            # Fallback if aioconsole not installed
            user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "shutdown"):
            print("\nJARVIS: Shutting down. Goodbye, sir.")
            break

        if user_input.lower() == "status":
            import json
            print(json.dumps(jarvis.status(), indent=2, default=str))
            continue

        if user_input.lower() == "tasks":
            print(jarvis.tasks.summary())
            continue

        if user_input.lower() == "agents":
            print(jarvis.agents.summary())
            continue

        # Stream response
        print("JARVIS: ", end="", flush=True)
        async for segment in jarvis.chat_stream(user_input):
            if segment["type"] == "text":
                print(segment["content"], end="", flush=True)
            elif segment["type"] == "tool_call":
                print(f"\n[ACTION: {segment['tool']}]", end="", flush=True)
        print("\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    jarvis = await boot()

    # Determine run mode
    import sys
    args = sys.argv[1:]

    if "--cli" in args or not jarvis.ui:
        # Terminal mode
        await run_cli(jarvis)
    else:
        # UI mode — start the web server
        import webbrowser
        ui_cfg = jarvis.config.get("ui", {})
        host = ui_cfg.get("host", "127.0.0.1")
        port = ui_cfg.get("port", 8090)
        url = f"http://{host}:{port}"

        logger.info(f"Starting UI at {url}")

        if ui_cfg.get("open_browser_on_start", True):
            # Non-blocking sleep in async
            await asyncio.sleep(1)
            webbrowser.open(url)

        try:
            # Shared event loop for Core and UI
            await jarvis.ui.serve()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            jarvis.say("Shutting down. Goodbye, sir.")

    # Cleanup
    if jarvis.tasks:
        jarvis.tasks.stop()
    if jarvis.agents:
        jarvis.agents.stop()

    logger.info("JARVIS offline.")


if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
