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
        """
        Return the latest cached stats.
        If no stats exist yet, perform a quick initial collection.
        """
        if not self._last_stats:
            return self._update_stats()
        return self._last_stats

    def _update_stats(self) -> dict:
        """Perform the actual heavy lifting of stats collection."""
        stats = {}
        try:
            import psutil
            import os

            # System-wide metrics
            stats["cpu_percent"] = psutil.cpu_percent(interval=None) # Non-blocking for the loop
            stats["cpu_count"] = psutil.cpu_count()
            stats["cpu_cores"] = psutil.cpu_percent(percpu=True)

            ram = psutil.virtual_memory()
            stats["ram_total_gb"] = round(ram.total / 1024**3, 1)
            stats["ram_used_gb"] = round(ram.used / 1024**3, 1)
            stats["ram_percent"] = ram.percent

            disk = psutil.disk_usage("/")
            stats["disk_total_gb"] = round(disk.total / 1024**3, 1)
            stats["disk_used_gb"] = round(disk.used / 1024**3, 1)
            stats["disk_percent"] = disk.percent

            # JARVIS process metrics
            proc = psutil.Process(os.getpid())
            # For process CPU, calling it with interval=None returns percentage since last call
            stats["jarvis_cpu"] = proc.cpu_percent(interval=2)
            stats["jarvis_ram_mb"] = round(proc.memory_info().rss / 1024**2, 1)

        except ImportError:
            logger.warning("psutil not installed — metrics unavailable.")
        except Exception as e:
            logger.error(f"Stats collection error: {e}")

        # GPU metrics
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

        # CPU Temperature metrics
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                # Common Linux keys for CPU temp
                for name in ["coretemp", "cpu_thermal", "k10temp", "acpitz"]:
                    if name in temps:
                        # Take the first sensor in the list (usually 'Package id 0' or 'temp1')
                        stats["cpu_temp_c"] = temps[name][0].current
                        break
        except Exception:
            pass

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
        from core.cognition import cognition
        
        # 1. Standard Resources
        checks = [
            ("cpu",  stats.get("cpu_percent", 0),  self.cpu_threshold,  "CPU usage at {val:.0f}%", "resource_exhaustion"),
            ("ram",  stats.get("ram_percent", 0),  self.ram_threshold,  "RAM usage at {val:.0f}%", "resource_exhaustion"),
            ("vram", stats.get("vram_percent", 0), self.vram_threshold, "VRAM usage at {val:.0f}%", "resource_exhaustion"),
        ]

        for key, val, threshold, msg_tpl, trigger_name in checks:
            if val >= threshold:
                last = self._alert_cooldown.get(key, 0)
                if now - last > self.ALERT_COOLDOWN_S:
                    self._alert_cooldown[key] = now
                    msg = msg_tpl.format(val=val)
                    logger.warning(f"System alert: {msg}")
                    # Notify Cognition Loop
                    cognition.trigger(trigger_name, {"metric": key, "value": val})

        # 2. Temperature (Emergency)
        if stats.get("gpu_temp_c", 0) > 85 or stats.get("cpu_temp_c", 0) > 90:
            last = self._alert_cooldown.get("temp", 0)
            if now - last > 60: # Short cooldown for emergencies
                self._alert_cooldown["temp"] = now
                cognition.trigger("system_overheat", {"stats": stats})

        if stats.get("disk_percent", 0) > 95:
            last = self._alert_cooldown.get("disk", 0)
            if now - last > 3600:
                self._alert_cooldown["disk"] = now
                cognition.trigger("resource_exhaustion", {"msg": "Disk space critically low (<5%)"})

        # 4. Throttling Detection (Actionable)
        if stats.get("cpu_freq_percent", 100) < 60:
             last = self._alert_cooldown.get("throttling", 0)
             if now - last > 900:
                 self._alert_cooldown["throttling"] = now
                 cognition.trigger("hardware_throttling", {"val": stats["cpu_freq_percent"]})

        # 5. Network Instability
        if stats.get("net_latency_ms", 0) > 300:
             last = self._alert_cooldown.get("network", 0)
             if now - last > 300:
                 self._alert_cooldown["network"] = now
                 cognition.trigger("network_instability", {"latency": stats["net_latency_ms"]})

    def _get_net_latency(self) -> float:
        """Measure latency to a stable target (1.1.1.1)."""
        import subprocess
        try:
            # -c 1 (1 packet), -W 1 (1s timeout)
            res = subprocess.check_output(["ping", "-c", "1", "-W", "1", "1.1.1.1"], stderr=subprocess.STDOUT, text=True)
            # Parse time=XX ms
            import re
            m = re.search(r"time=([\d\.]+)", res)
            return float(m.group(1)) if m else 0.0
        except Exception:
            return 999.0 # Fail = high latency

    # ------------------------------------------------------------------
    # Background monitor
    # ------------------------------------------------------------------

    def start(self, interval: Optional[int] = None):
        if interval is not None:
            self.check_interval = interval
            
        if self._running:
            return
        self._running = True
        # Seed the CPU measurements for both system and process
        import psutil
        import os
        psutil.cpu_percent(interval=None)
        psutil.Process(os.getpid()).cpu_percent(interval=None)
        
        self._thread = threading.Thread(target=self._loop, daemon=True, name="sys-monitor")
        self._thread.start()
        logger.info(f"System monitor started (interval: {self.check_interval}s)")

    def stop(self):
        self._running = False
        logger.info("System monitor stopped.")

    def _loop(self):
        while self._running:
            try:
                stats = self._update_stats()
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
