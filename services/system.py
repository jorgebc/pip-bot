"""System health monitoring service."""

import asyncio
import psutil
from dataclasses import dataclass
from datetime import datetime, timedelta

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
