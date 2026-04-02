"""System health monitoring service."""

import asyncio
import psutil
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SystemStatus:
    """System health metrics."""

    uptime: str  # Human-readable uptime string
    cpu_percent: float  # CPU usage percentage (0-100)
    ram_percent: float  # RAM usage percentage (0-100)
    ram_used_gb: float  # RAM used in GB
    ram_total_gb: float  # Total RAM in GB
    disk_percent: float  # Disk usage percentage (0-100)
    disk_used_gb: float  # Disk used in GB
    disk_total_gb: float  # Total disk in GB


def get_system_status() -> SystemStatus:
    """
    Collect current system health metrics (BLOCKING - use async version in Discord cogs).

    Returns:
        SystemStatus object with CPU, RAM, disk, and uptime information.

    Raises:
        Exception: If system metrics cannot be collected.
    """
    try:
        # Get uptime
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime_delta = datetime.now() - boot_time
        uptime_str = _format_timedelta(uptime_delta)

        # Get CPU usage (non-blocking instantaneous value)
        cpu_percent = psutil.cpu_percent(interval=None)

        # Get RAM usage
        ram = psutil.virtual_memory()
        ram_percent = ram.percent
        ram_used_gb = ram.used / (1024**3)
        ram_total_gb = ram.total / (1024**3)

        # Get disk usage (root filesystem)
        disk = psutil.disk_usage("/")
        disk_percent = disk.percent
        disk_used_gb = disk.used / (1024**3)
        disk_total_gb = disk.total / (1024**3)

        return SystemStatus(
            uptime=uptime_str,
            cpu_percent=cpu_percent,
            ram_percent=ram_percent,
            ram_used_gb=ram_used_gb,
            ram_total_gb=ram_total_gb,
            disk_percent=disk_percent,
            disk_used_gb=disk_used_gb,
            disk_total_gb=disk_total_gb,
        )
    except Exception as e:
        logger.error(f"Failed to collect system metrics: {e}", exc_info=True)
        raise


async def get_system_status_async() -> SystemStatus:
    """
    Collect current system health metrics asynchronously.

    Runs blocking psutil calls in a thread pool to avoid blocking the event loop.

    Returns:
        SystemStatus object with CPU, RAM, disk, and uptime information.

    Raises:
        Exception: If system metrics cannot be collected.
    """
    loop = asyncio.get_event_loop()
    try:
        status = await loop.run_in_executor(None, get_system_status)
        return status
    except Exception as e:
        logger.error(f"Failed to collect system metrics asynchronously: {e}", exc_info=True)
        raise


_THERMAL_PATH = Path("/sys/class/thermal/thermal_zone0/temp")


def get_cpu_temperature() -> float:
    """
    Read the CPU temperature from the thermal subsystem (BLOCKING).

    Reads millidegree Celsius value from ``/sys/class/thermal/thermal_zone0/temp``
    and converts it to degrees Celsius.

    Returns:
        CPU temperature in degrees Celsius.

    Raises:
        FileNotFoundError: If the thermal zone file does not exist (non-Linux or
            non-RPi system).
        OSError: If the file cannot be read.
        ValueError: If the file contents cannot be parsed as a number.
    """
    try:
        raw = _THERMAL_PATH.read_text(encoding="utf-8").strip()
        temp_c = int(raw) / 1000.0
        logger.debug(f"CPU temperature: {temp_c:.1f}°C")
        return temp_c
    except FileNotFoundError:
        logger.error(f"Thermal zone file not found: {_THERMAL_PATH}")
        raise
    except (OSError, ValueError) as e:
        logger.error(f"Failed to read CPU temperature: {e}", exc_info=True)
        raise


async def get_cpu_temperature_async() -> float:
    """
    Read the CPU temperature asynchronously.

    Runs the blocking file read in a thread pool to avoid blocking the event loop.

    Returns:
        CPU temperature in degrees Celsius.

    Raises:
        FileNotFoundError: If the thermal zone file does not exist.
        OSError: If the file cannot be read.
        ValueError: If the file contents cannot be parsed as a number.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_cpu_temperature)


def _format_timedelta(delta: timedelta) -> str:
    """
    Format a timedelta into a human-readable string.

    Args:
        delta: The timedelta to format.

    Returns:
        Formatted string like "5d 3h 42m"
    """
    total_seconds = int(delta.total_seconds())
    days = total_seconds // (24 * 3600)
    hours = (total_seconds % (24 * 3600)) // 3600
    minutes = (total_seconds % 3600) // 60

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")

    return " ".join(parts) if parts else "0m"
