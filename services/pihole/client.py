"""Pi-hole local API client for status, enable, disable, and top-domains queries."""

import hashlib
import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from utils.concurrency import run_blocking
from utils.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_HOST = "localhost"
_DEFAULT_PORT = 80
_DEFAULT_TOP_N = 5


@dataclass
class PiholeStatus:
    """Pi-hole status and summary metrics for today."""

    enabled: bool  # Whether ad blocking is currently active
    total_queries: int  # Total DNS queries today
    blocked_queries: int  # Blocked queries today
    blocked_percent: float  # Percentage of queries blocked today
    domains_blocked: int  # Number of domains in the block list


@dataclass
class PiholeTopData:
    """Top DNS queries and top blocked domains from Pi-hole."""

    top_queries: dict[str, int] = field(default_factory=dict)  # domain → query count
    top_ads: dict[str, int] = field(default_factory=dict)  # domain → block count


def _compute_auth(password: str) -> str:
    """
    Compute the Pi-hole API auth token from the admin password.

    Pi-hole v5 uses the double-MD5 of the web admin password as the API token.

    Args:
        password: Raw web admin password set in the Pi-hole UI.

    Returns:
        Double-MD5 hex digest to pass as the ``auth`` query parameter.
    """
    first = hashlib.md5(password.encode()).hexdigest()  # nosec B324
    return hashlib.md5(first.encode()).hexdigest()  # nosec B324


def _api_get(host: str, port: int, params: str) -> dict | list:
    """
    Perform a GET request to the Pi-hole local API (BLOCKING).

    Args:
        host: Pi-hole hostname or IP (e.g. ``"localhost"``).
        port: Pi-hole HTTP port (e.g. ``80``).
        params: URL query string without the leading ``?``.

    Returns:
        Parsed JSON response — a dict for most endpoints, a list if Pi-hole
        returns an empty response (high privacy level).

    Raises:
        urllib.error.URLError: If the connection fails or times out.
        ValueError: If the response body is not valid JSON.
    """
    url = f"http://{host}:{port}/admin/api.php?{params}"
    # Omit auth token from log output to avoid leaking it
    log_url = url.split("&auth")[0].split("?auth")[0]
    logger.debug(f"Pi-hole API GET: {log_url}")
    try:
        with urllib.request.urlopen(url, timeout=10) as response:  # nosec B310
            body = response.read().decode("utf-8")
    except urllib.error.URLError as e:
        logger.error(f"Pi-hole API unreachable at {host}:{port} — {e}")
        raise
    try:
        return json.loads(body)
    except json.JSONDecodeError as e:
        logger.error(f"Pi-hole API returned invalid JSON: {e}")
        raise ValueError(f"Pi-hole API returned invalid JSON: {e}") from e


def get_pihole_status(host: str = _DEFAULT_HOST, port: int = _DEFAULT_PORT) -> PiholeStatus:
    """
    Retrieve Pi-hole status and today's query summary (BLOCKING).

    Uses the unauthenticated ``?summary`` endpoint — no password required.

    Args:
        host: Pi-hole hostname or IP address.
        port: Pi-hole HTTP port.

    Returns:
        PiholeStatus dataclass with enabled state and DNS query counts.

    Raises:
        urllib.error.URLError: If the Pi-hole API is unreachable.
        ValueError: If the API response is malformed or not JSON.
    """
    data = _api_get(host, port, "summary")
    if not isinstance(data, dict):
        raise ValueError(f"Unexpected Pi-hole summary response type: {type(data)}")
    try:
        enabled = data.get("status", "disabled") == "enabled"
        total_queries = int(data.get("dns_queries_today", 0))
        blocked_queries = int(data.get("ads_blocked_today", 0))
        blocked_percent = float(data.get("ads_percentage_today", 0.0))
        domains_blocked = int(data.get("domains_being_blocked", 0))
    except (TypeError, ValueError) as e:
        logger.error(f"Failed to parse Pi-hole summary response: {e}")
        raise ValueError(f"Malformed Pi-hole summary response: {e}") from e
    return PiholeStatus(
        enabled=enabled,
        total_queries=total_queries,
        blocked_queries=blocked_queries,
        blocked_percent=blocked_percent,
        domains_blocked=domains_blocked,
    )


async def get_pihole_status_async(
    host: str = _DEFAULT_HOST, port: int = _DEFAULT_PORT
) -> PiholeStatus:
    """
    Retrieve Pi-hole status asynchronously.

    Wraps the blocking HTTP call in a thread-pool executor.

    Args:
        host: Pi-hole hostname or IP address.
        port: Pi-hole HTTP port.

    Returns:
        PiholeStatus dataclass.

    Raises:
        urllib.error.URLError: If the Pi-hole API is unreachable.
        ValueError: If the API response is malformed.
    """
    return await run_blocking(get_pihole_status, host, port)


def enable_pihole(host: str, port: int, password: str) -> None:
    """
    Enable Pi-hole ad blocking (BLOCKING).

    Args:
        host: Pi-hole hostname or IP address.
        port: Pi-hole HTTP port.
        password: Web admin password (used to derive the API auth token).

    Raises:
        urllib.error.URLError: If the Pi-hole API is unreachable.
        ValueError: If the API response does not confirm the enabled state.
    """
    auth = _compute_auth(password)
    data = _api_get(host, port, f"enable&auth={auth}")
    if not isinstance(data, dict) or data.get("status") != "enabled":
        raise ValueError(f"Pi-hole enable did not return expected status: {data}")
    logger.info("Pi-hole ad blocking enabled")


async def enable_pihole_async(host: str, port: int, password: str) -> None:
    """
    Enable Pi-hole ad blocking asynchronously.

    Args:
        host: Pi-hole hostname or IP address.
        port: Pi-hole HTTP port.
        password: Web admin password.

    Raises:
        urllib.error.URLError: If the Pi-hole API is unreachable.
        ValueError: If the API response does not confirm the enabled state.
    """
    await run_blocking(enable_pihole, host, port, password)


def disable_pihole(host: str, port: int, password: str, seconds: int = 0) -> None:
    """
    Disable Pi-hole ad blocking (BLOCKING).

    Args:
        host: Pi-hole hostname or IP address.
        port: Pi-hole HTTP port.
        password: Web admin password.
        seconds: Duration to disable in seconds; ``0`` means indefinitely.

    Raises:
        urllib.error.URLError: If the Pi-hole API is unreachable.
        ValueError: If the API response does not confirm the disabled state.
    """
    auth = _compute_auth(password)
    data = _api_get(host, port, f"disable={seconds}&auth={auth}")
    if not isinstance(data, dict) or data.get("status") != "disabled":
        raise ValueError(f"Pi-hole disable did not return expected status: {data}")
    duration = f"{seconds}s" if seconds > 0 else "indefinitely"
    logger.info(f"Pi-hole ad blocking disabled ({duration})")


async def disable_pihole_async(
    host: str, port: int, password: str, seconds: int = 0
) -> None:
    """
    Disable Pi-hole ad blocking asynchronously.

    Args:
        host: Pi-hole hostname or IP address.
        port: Pi-hole HTTP port.
        password: Web admin password.
        seconds: Duration to disable in seconds; ``0`` means indefinitely.

    Raises:
        urllib.error.URLError: If the Pi-hole API is unreachable.
        ValueError: If the API response does not confirm the disabled state.
    """
    await run_blocking(disable_pihole, host, port, password, seconds)


def get_pihole_top(
    host: str, port: int, password: str, n: int = _DEFAULT_TOP_N
) -> PiholeTopData:
    """
    Retrieve the top queried and top blocked domains from Pi-hole (BLOCKING).

    Requires authentication because top-domains data is privacy-sensitive.

    Args:
        host: Pi-hole hostname or IP address.
        port: Pi-hole HTTP port.
        password: Web admin password.
        n: Number of top entries to retrieve per category (default 5).

    Returns:
        PiholeTopData with ``top_queries`` and ``top_ads`` dicts (domain → count).

    Raises:
        urllib.error.URLError: If the Pi-hole API is unreachable.
        ValueError: If the API returns an empty response (privacy level too high)
            or cannot be parsed.
    """
    auth = _compute_auth(password)
    data = _api_get(host, port, f"topItems={n}&auth={auth}")
    if isinstance(data, list):
        # Pi-hole returns [] when the privacy level blocks top-domain disclosure
        raise ValueError(
            "Pi-hole returned no data — privacy level may be set too high"
        )
    if not isinstance(data, dict):
        raise ValueError(f"Unexpected Pi-hole top-items response type: {type(data)}")
    return PiholeTopData(
        top_queries=dict(data.get("top_queries", {})),
        top_ads=dict(data.get("top_ads", {})),
    )


async def get_pihole_top_async(
    host: str, port: int, password: str, n: int = _DEFAULT_TOP_N
) -> PiholeTopData:
    """
    Retrieve top queried and top blocked domains asynchronously.

    Args:
        host: Pi-hole hostname or IP address.
        port: Pi-hole HTTP port.
        password: Web admin password.
        n: Number of top entries per category (default 5).

    Returns:
        PiholeTopData with ``top_queries`` and ``top_ads`` dicts.

    Raises:
        urllib.error.URLError: If the Pi-hole API is unreachable.
        ValueError: If the response is empty or cannot be parsed.
    """
    return await run_blocking(get_pihole_top, host, port, password, n)
