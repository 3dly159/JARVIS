"""
core/agent_manager.py - JARVIS Agent Manager

Manages up to 20 agents, 5 running in parallel.
Each agent is an autonomous worker with its own brain context and task.
Agents can be spawned, monitored, steered, and killed.
"""

import logging
import threading
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Callable

logger = logging.getLogger("jarvis.agent_manager")

MAX_AGENTS = 20
MAX_PARALLEL = 5


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AgentStatus(str, Enum):
    IDLE      = "idle"
    RUNNING   = "running"
    WAITING   = "waiting"
    DONE      = "done"
    FAILED    = "failed"
    KILLED    = "killed"


class AgentType(str, Enum):
    RESEARCHER = "researcher"
    EXECUTOR   = "executor"
    WRITER     = "writer"
    MONITOR    = "monitor"
    ANALYST    = "analyst"
    PLANNER    = "planner"
    GENERAL    = "general"


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class Agent:
    """A single JARVIS sub-agent running in its own thread."""

    def __init__(
        self,
        name: str,
        agent_type: AgentType = AgentType.GENERAL,
        task: str = "",
        system_context: str = "",
        on_message: Optional[Callable] = None,
        on_done: Optional[Callable] = None,
        on_fail: Optional[Callable] = None,
        agent_id: Optional[str] = None,
    ):
        self.id = agent_id or str(uuid.uuid4())[:8]
        self.name = name
        self.type = agent_type
        self.task = task
        self.system_context = system_context
        self.status = AgentStatus.IDLE
        self.created = datetime.now().isoformat()
        self.started: Optional[str] = None
        self.finished: Optional[str] = None
        self.result: str = ""
        self.error: str = ""
        self.log: list[dict] = []
        self.messages: list[dict] = []
        self.on_message = on_message
        self.on_done = on_done
        self.on_fail = on_fail
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def _log(self, entry: str, level: str = "info"):
        self.log.append({"time": datetime.now().isoformat(), "level": level, "entry": entry})
        getattr(logger, level, logger.info)(f"[Agent:{self.name}] {entry}")

    def _run(self, work_fn: Callable):
        self.status = AgentStatus.RUNNING
        self.started = datetime.now().isoformat()
        self._log(f"Starting: {self.task[:80]}")
        try:
            result = work_fn(self)
            self.result = result or ""
            self.status = AgentStatus.DONE
            self.finished = datetime.now().isoformat()
            self._log(f"Done. Result: {self.result[:80]}")
            if self.on_done:
                self.on_done(self, self.result)
        except Exception as e:
            self.error = str(e)
            self.status = AgentStatus.FAILED
            self.finished = datetime.now().isoformat()
            self._log(f"Failed: {e}", level="error")
            if self.on_fail:
                self.on_fail(self, self.error)

    def start(self, work_fn: Callable):
        self._thread = threading.Thread(
            target=self._run, args=(work_fn,), daemon=True, name=f"agent-{self.name}"
        )
        self._thread.start()

    def kill(self):
        self._stop_event.set()
        self.status = AgentStatus.KILLED
        self.finished = datetime.now().isoformat()
        self._log("Killed.", level="warning")

    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def should_stop(self) -> bool:
        """Work functions poll this to respect kill signals."""
        return self._stop_event.is_set()

    def receive_message(self, sender: str, content: str):
        self.messages.append({"from": sender, "content": content, "time": datetime.now().isoformat()})
        self._log(f"Message from {sender}: {content[:60]}")
        if self.on_message:
            self.on_message(self, sender, content)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "task": self.task,
            "status": self.status.value,
            "created": self.created,
            "started": self.started,
            "finished": self.finished,
            "result": self.result[:200] if self.result else "",
            "error": self.error,
            "log_entries": len(self.log),
            "messages": len(self.messages),
        }

    def __repr__(self):
        return f"Agent({self.id}, '{self.name}', {self.type.value}, {self.status.value})"


# ---------------------------------------------------------------------------
# Built-in work functions
# ---------------------------------------------------------------------------

def llm_work(prompt: str, system: str = "") -> Callable:
    """Work function: ask the brain a question, return the answer."""
    def work_fn(agent: Agent) -> str:
        from core.brain import brain
        agent._log(f"Asking brain: {prompt[:80]}")
        return brain.think(prompt=prompt, system=system or None)
    return work_fn


def research_work(query: str) -> Callable:
    """Work function: research a topic and return a summary."""
    def work_fn(agent: Agent) -> str:
        from core.brain import brain
        agent._log(f"Researching: {query}")
        return brain.think(f"Research the following thoroughly and summarise:\n\n{query}")
    return work_fn


def monitor_work(check_fn: Callable, interval: int = 30) -> Callable:
    """
    Work function: repeatedly call check_fn(agent) every `interval` seconds
    until the agent is killed or check_fn returns a non-None result.
    """
    def work_fn(agent: Agent) -> str:
        agent._log(f"Monitor started (interval: {interval}s)")
        while not agent.should_stop():
            result = check_fn(agent)
            if result is not None:
                return result
            time.sleep(interval)
        return "Monitor stopped."
    return work_fn


# ---------------------------------------------------------------------------
# Agent Manager
# ---------------------------------------------------------------------------

class AgentManager:
    """
    JARVIS Agent Manager.
    Pool of up to MAX_AGENTS agents, MAX_PARALLEL running simultaneously.
    Idle agents are queued and auto-started when a slot opens.
    """

    def __init__(
        self,
        max_agents: int = MAX_AGENTS,
        max_parallel: int = MAX_PARALLEL,
        on_agent_done: Optional[Callable] = None,
    ):
        self.max_agents = max_agents
        self.max_parallel = max_parallel
        self.on_agent_done = on_agent_done
        self._agents: dict[str, Agent] = {}
        self._work_fns: dict[str, Callable] = {}   # agent_id → work_fn (for queue)
        self._lock = threading.Lock()
        self._queue_thread: Optional[threading.Thread] = None
        self._running = False
        logger.info(f"Agent manager online. Max: {max_agents}, parallel: {max_parallel}")

    # ----- Spawn -----

    def spawn(
        self,
        name: str,
        task: str,
        work_fn: Optional[Callable] = None,
        agent_type: AgentType = AgentType.GENERAL,
        system_context: str = "",
        on_done: Optional[Callable] = None,
        on_fail: Optional[Callable] = None,
    ) -> Optional[Agent]:
        """
        Spawn a new agent. Auto-queues if parallel limit is reached.
        Returns the Agent or None if the pool is full.
        """
        with self._lock:
            active_count = len(self._agents)
            if active_count >= self.max_agents:
                logger.warning(f"Agent pool full ({self.max_agents}). Cannot spawn '{name}'.")
                return None

            agent = Agent(
                name=name,
                agent_type=agent_type,
                task=task,
                system_context=system_context,
                on_done=self._wrap_done(on_done),
                on_fail=on_fail,
            )
            self._agents[agent.id] = agent

            # Default work function: ask the brain
            wfn = work_fn or llm_work(task, system_context)
            self._work_fns[agent.id] = wfn

            running_count = self._running_count()
            if running_count < self.max_parallel:
                agent.start(wfn)
                logger.info(f"Spawned + started: {agent} ({running_count + 1}/{self.max_parallel} slots)")
            else:
                logger.info(f"Spawned (queued): {agent} — waiting for slot")

            return agent

    # ----- Control -----

    def kill(self, agent_id: str):
        agent = self._agents.get(agent_id)
        if agent:
            agent.kill()
            logger.info(f"Killed agent {agent_id}")

    def kill_all(self):
        for agent in self._agents.values():
            if agent.status == AgentStatus.RUNNING:
                agent.kill()
        logger.info("All running agents killed.")

    def message(self, agent_id: str, sender: str, content: str):
        """Send a message to a specific agent."""
        agent = self._agents.get(agent_id)
        if agent:
            agent.receive_message(sender, content)
        else:
            logger.warning(f"Agent {agent_id} not found for message.")

    def broadcast(self, sender: str, content: str, status_filter: AgentStatus = AgentStatus.RUNNING):
        """Broadcast a message to all agents matching a status."""
        for agent in self._agents.values():
            if agent.status == status_filter:
                agent.receive_message(sender, content)

    def get(self, agent_id: str) -> Optional[Agent]:
        return self._agents.get(agent_id)

    def list_all(self) -> list[Agent]:
        return list(self._agents.values())

    def list_running(self) -> list[Agent]:
        return [a for a in self._agents.values() if a.status == AgentStatus.RUNNING]

    def list_idle(self) -> list[Agent]:
        return [a for a in self._agents.values() if a.status == AgentStatus.IDLE]

    def cleanup(self):
        """Remove finished/killed/failed agents from the pool."""
        with self._lock:
            finished = [
                aid for aid, a in self._agents.items()
                if a.status in (AgentStatus.DONE, AgentStatus.FAILED, AgentStatus.KILLED)
            ]
            for aid in finished:
                del self._agents[aid]
                self._work_fns.pop(aid, None)
            if finished:
                logger.info(f"Cleaned up {len(finished)} finished agent(s).")

    # ----- Queue management -----

    def _running_count(self) -> int:
        return sum(1 for a in self._agents.values() if a.status == AgentStatus.RUNNING)

    def _wrap_done(self, user_callback: Optional[Callable]) -> Callable:
        """Wraps the done callback to trigger queue processing."""
        def handler(agent: Agent, result: str):
            logger.info(f"Agent done: {agent.name} → promoting queued agents")
            if self.on_agent_done:
                self.on_agent_done(agent, result)
            if user_callback:
                user_callback(agent, result)
            self._promote_queued()
        return handler

    def _promote_queued(self):
        """Start idle agents if parallel slots are available."""
        with self._lock:
            for agent in self._agents.values():
                if self._running_count() >= self.max_parallel:
                    break
                if agent.status == AgentStatus.IDLE:
                    wfn = self._work_fns.get(agent.id)
                    if wfn:
                        agent.start(wfn)
                        logger.info(f"Promoted queued agent: {agent}")

    # ----- Background monitor -----

    def start(self):
        """Start background queue monitor."""
        if self._running:
            return
        self._running = True
        self._queue_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._queue_thread.start()
        logger.info("Agent manager monitor started.")

    def stop(self):
        self._running = False
        self.kill_all()
        logger.info("Agent manager stopped.")

    def _monitor_loop(self):
        """Periodically promote queued agents and clean up finished ones."""
        while self._running:
            time.sleep(5)
            try:
                self._promote_queued()
                self.cleanup()
            except Exception as e:
                logger.error(f"Agent monitor error: {e}")

    # ----- Summary -----

    def summary(self) -> str:
        agents = self.list_all()
        if not agents:
            return "No agents in pool."
        lines = [f"Agents ({len(agents)}/{self.max_agents}, {self._running_count()}/{self.max_parallel} running):"]
        for a in agents:
            lines.append(f"  [{a.id}] {a.name} | {a.type.value} | {a.status.value}")
        return "\n".join(lines)

    def status(self) -> dict:
        agents = self.list_all()
        return {
            "total": len(agents),
            "running": self._running_count(),
            "idle": len(self.list_idle()),
            "done": sum(1 for a in agents if a.status == AgentStatus.DONE),
            "failed": sum(1 for a in agents if a.status == AgentStatus.FAILED),
            "max_agents": self.max_agents,
            "max_parallel": self.max_parallel,
            "monitor_running": self._running,
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

agent_manager = AgentManager()


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Testing JARVIS agent manager...\n")

    results = []

    def on_done(agent, result):
        results.append((agent.name, result))
        print(f"\n✅ {agent.name} finished: {result[:80]}")

    # Spawn 3 agents (only 2 run in parallel with max_parallel=2 for test)
    manager = AgentManager(max_agents=20, max_parallel=2)
    manager.start()

    for i in range(1, 4):
        a = manager.spawn(
            name=f"worker-{i}",
            task=f"Task {i}: count to 3 slowly.",
            work_fn=llm_work(f"Reply with exactly: 'Agent {i} reporting in.'"),
            agent_type=AgentType.GENERAL,
            on_done=on_done,
        )
        print(f"Spawned: {a}")

    print(f"\nStatus: {manager.status()}")
    print("\nWaiting for agents to finish (up to 30s)...")
    time.sleep(30)

    print(f"\nFinal status: {manager.status()}")
    print(f"Results collected: {len(results)}")
    for name, result in results:
        print(f"  {name}: {result[:80]}")

    manager.stop()
