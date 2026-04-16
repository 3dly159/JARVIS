"""
system/monitor.py - JARVIS System Monitor

Watches CPU, RAM, VRAM, disk, and JARVIS process health.
Fires alerts when thresholds exceeded.
Feeds health summary to brain context.

Usage:
    from system.monitor import monitor
    stats = monitor.get_stats()
    monitor.start()
    monitor.stop()
"""

import logging
import threading
import time
from typing import Callable, Optional

logger = logging.getLogger("jarvis.monitor")


class SystemMonitor:
    """Monitors system resources and fires alerts on threshold breaches."""

    def __init__(
        self,
        check_interval: int = 30,
        cpu_threshold: float = 90.0,
        ram_threshold: float = 85.0,
        vram_threshold: float = 90.0,
        on_alert: Optional[Callable] = None,
    ):
        self.check_interval = check_interval
        self.cpu_threshold = cpu_threshold
        self.ram_threshold = ram_threshold
        self.vram_threshold = vram_threshold
        self.on_alert = on_alert
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_stats: dict = {}
        self._alert_cooldown: dict = {}   # metric → last alert time
        self.ALERT_COOLDOWN_S = 300       # 5 min between same alert

    # ------------------------------------------------------------------
    # Stats collection
    # ------------------------------------------------------------------

    def get_stats(self) -> dict:
        """Collect current system stats."""
        stats = {}
        try:
            import psutil

            # CPU
            stats["cpu_percent"] = psutil.cpu_percent(interval=1)
            stats["cpu_count"] = psutil.cpu_count()

            # RAM
            ram = psutil.virtual_memory()
            stats["ram_total_gb"] = round(ram.total / 1024**3, 1)
            stats["ram_used_gb"] = round(ram.used / 1024**3, 1)
            stats["ram_percent"] = ram.percent

            # Disk
            disk = psutil.disk_usage("/")
            stats["disk_total_gb"] = round(disk.total / 1024**3, 1)
            stats["disk_used_gb"] = round(disk.used / 1024**3, 1)
            stats["disk_percent"] = disk.percent

            # JARVIS process
            import os
            proc = psutil.Process(os.getpid())
            stats["jarvis_cpu"] = proc.cpu_percent(interval=0.1)
            stats["jarvis_ram_mb"] = round(proc.memory_info().rss / 1024**2, 1)

        except ImportError:
            logger.warning("psutil not installed — CPU/RAM monitoring unavailable.")
        except Exception as e:
            logger.error(f"Stats collection error: {e}")

        # VRAM
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
            stats["vram_total_gb"] = round(mem.total / 1024**3, 1)
            stats["vram_used_gb"] = round(mem.used / 1024**3, 1)
            stats["vram_percent"] = round(mem.used / mem.total * 100, 1)
            temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            stats["gpu_temp_c"] = temp
        except Exception:
            stats["vram_available"] = False

        self._last_stats = stats
        return stats

    def get_summary(self) -> str:
        """Returns a human-readable system summary for brain context."""
        s = self._last_stats or self.get_stats()
        lines = ["System status:"]
        if "cpu_percent" in s:
            lines.append(f"  CPU: {s['cpu_percent']}%")
            lines.append(f"  RAM: {s['ram_used_gb']}GB / {s['ram_total_gb']}GB ({s['ram_percent']}%)")
            lines.append(f"  Disk: {s['disk_used_gb']}GB / {s['disk_total_gb']}GB ({s['disk_percent']}%)")
            lines.append(f"  JARVIS process: {s.get('jarvis_cpu', '?')}% CPU, {s.get('jarvis_ram_mb', '?')}MB RAM")
        if "vram_percent" in s:
            lines.append(f"  VRAM: {s['vram_used_gb']}GB / {s['vram_total_gb']}GB ({s['vram_percent']}%)")
            if "gpu_temp_c" in s:
                lines.append(f"  GPU temp: {s['gpu_temp_c']}°C")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Threshold checks
    # ------------------------------------------------------------------

    def _check_thresholds(self, stats: dict):
        now = time.time()
        alerts = []

        checks = [
            ("cpu",  stats.get("cpu_percent", 0),  self.cpu_threshold,  "CPU usage at {val:.0f}%"),
            ("ram",  stats.get("ram_percent", 0),  self.ram_threshold,  "RAM usage at {val:.0f}%"),
            ("vram", stats.get("vram_percent", 0), self.vram_threshold, "VRAM usage at {val:.0f}%"),
        ]

        for key, val, threshold, msg_tpl in checks:
            if val >= threshold:
                last = self._alert_cooldown.get(key, 0)
                if now - last > self.ALERT_COOLDOWN_S:
                    self._alert_cooldown[key] = now
                    msg = msg_tpl.format(val=val)
                    alerts.append({"metric": key, "value": val, "threshold": threshold, "message": msg})
                    logger.warning(f"System alert: {msg}")

        for alert in alerts:
            if self.on_alert:
                self.on_alert(alert)

    # ------------------------------------------------------------------
    # Background monitor
    # ------------------------------------------------------------------

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="sys-monitor")
        self._thread.start()
        logger.info(f"System monitor started (interval: {self.check_interval}s)")

    def stop(self):
        self._running = False
        logger.info("System monitor stopped.")

    def _loop(self):
        while self._running:
            try:
                stats = self.get_stats()
                self._check_thresholds(stats)
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
            time.sleep(self.check_interval)

    def status(self) -> dict:
        return {
            "running": self._running,
            "check_interval": self.check_interval,
            "thresholds": {
                "cpu": self.cpu_threshold,
                "ram": self.ram_threshold,
                "vram": self.vram_threshold,
            },
            "last_stats": self._last_stats,
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

from core.config_manager import config


def _on_system_alert(alert: dict):
    try:
        from core.jarvis import jarvis
        msg = f"Sir, {alert['message']} — exceeding {alert['threshold']}% threshold."
        if jarvis.notifier:
            jarvis.notifier.warning(msg)
        if jarvis.memory:
            jarvis.memory.log(msg, category="warning")
    except Exception:
        pass


monitor = SystemMonitor(
    check_interval=config.get("monitor.check_interval_seconds", 30),
    cpu_threshold=config.get("monitor.cpu_alert_threshold", 90),
    ram_threshold=config.get("monitor.ram_alert_threshold", 85),
    vram_threshold=config.get("monitor.vram_alert_threshold", 90),
    on_alert=_on_system_alert,
)
