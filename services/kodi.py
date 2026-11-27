"""Controls the Kodi systemd service."""

import subprocess

from utils.concurrency import run_blocking
from utils.logger import get_logger

logger = get_logger(__name__)

_KODI_ACTIONS = frozenset({"start", "stop", "restart", "status"})
_INACTIVE_STATES = frozenset(
    {"inactive", "failed", "activating", "deactivating", "reloading", "maintenance"}
)
_COMMAND_TIMEOUT_SECONDS = 10


def control_kodi_service(action: str) -> str:
    """Run an allowlisted action against the Kodi systemd service.

    Args:
        action: One of ``start``, ``stop``, ``restart``, or ``status``.

    Returns:
        For ``status``, ``"activo"`` or ``"parado"``. For other actions,
        the command's standard output.

    Raises:
        ValueError: If the action is not allowlisted.
        subprocess.CalledProcessError: If systemctl fails an operation.
        FileNotFoundError: If sudo or systemctl cannot be executed.
        subprocess.TimeoutExpired: If systemctl exceeds its timeout.
        RuntimeError: If ``is-active`` returns an unknown or inconsistent state.
    """
    if action not in _KODI_ACTIONS:
        raise ValueError(f"Unsupported Kodi action: {action}")

    systemctl_action = "is-active" if action == "status" else action
    command = ["sudo", "/usr/bin/systemctl", systemctl_action, "kodi"]
    logger.info("Running Kodi systemd action: %s", action)

    try:
        if action == "status":
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                shell=False,
                timeout=_COMMAND_TIMEOUT_SECONDS,
            )
            state = result.stdout.strip()
            if state == "active" and result.returncode == 0:
                return "activo"
            if state in _INACTIVE_STATES and result.returncode != 0:
                return "parado"
            logger.error(
                "Unexpected systemctl is-active result (exit %s, state %r): %s",
                result.returncode,
                state,
                result.stderr,
            )
            raise RuntimeError("systemctl returned an unexpected Kodi service state")

        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            shell=False,
            timeout=_COMMAND_TIMEOUT_SECONDS,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as error:
        logger.error(
            "systemctl Kodi action %s failed (exit %s): %s",
            action,
            error.returncode,
            error.stderr,
        )
        raise
    except FileNotFoundError:
        logger.error("Could not find sudo or /usr/bin/systemctl for Kodi action %s", action)
        raise
    except subprocess.TimeoutExpired:
        logger.error("systemctl Kodi action %s timed out", action)
        raise
    except OSError as error:
        logger.error("Could not execute systemctl Kodi action %s: %s", action, error)
        raise


async def control_kodi_service_async(action: str) -> str:
    """Run a Kodi systemd action without blocking the event loop.

    Args:
        action: One of ``start``, ``stop``, ``restart``, or ``status``.

    Returns:
        The result from :func:`control_kodi_service`.

    Raises:
        ValueError: If the action is not allowlisted.
        subprocess.CalledProcessError: If systemctl fails an operation.
        FileNotFoundError: If sudo or systemctl cannot be executed.
        subprocess.TimeoutExpired: If systemctl exceeds its timeout.
        RuntimeError: If ``is-active`` returns an unknown or inconsistent state.
    """
    return await run_blocking(control_kodi_service, action)
