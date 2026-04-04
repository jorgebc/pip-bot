"""Pi-hole v6 local REST API client.

Pi-hole v6 replaced the legacy ``api.php`` endpoint with a session-based
REST API rooted at ``/api/``.  Authentication flow:

1. ``POST /api/auth`` with the admin password → receive a session SID.
2. Send the SID as a ``Cookie: sid=<value>`` header on subsequent requests.
3. ``DELETE /api/auth`` to invalidate the session when done.
"""

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


# ---------------------------------------------------------------------------
# Internal HTTP helpers
# ---------------------------------------------------------------------------


def _authenticate(host: str, port: int, password: str) -> str:
    """
    Authenticate against the Pi-hole v6 API and return a session SID (BLOCKING).

    Posts the admin password to ``POST /api/auth`` and extracts the session
    identifier from the response.

    Args:
        host: Pi-hole hostname or IP address.
        port: Pi-hole HTTP port.
        password: Web admin password.

    Returns:
        Session SID string to pass as ``Cookie: sid=<value>`` in later calls.

    Raises:
        urllib.error.HTTPError: If authentication is rejected (e.g. HTTP 401).
        urllib.error.URLError: If the Pi-hole API is unreachable.
        ValueError: If the response is missing the expected SID field.
    """
    url = f"http://{host}:{port}/api/auth"
    body = json.dumps({"password": password}).encode()
    req = urllib.request.Request(url, data=body, method="POST")  # nosec B310
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # nosec B310
            data = json.loads(resp.read().decode())
    except urllib.error.URLError:
        raise
    sid = data.get("session", {}).get("sid")
    if not sid:
        raise ValueError(f"Pi-hole auth response missing SID: {data}")
    logger.debug("Pi-hole session authenticated")
    return sid


def _delete_session(host: str, port: int, sid: str) -> None:
    """
    Invalidate a Pi-hole session via ``DELETE /api/auth`` (BLOCKING, best-effort).

    Failures are logged at DEBUG level and silently swallowed — the session will
    expire on its own (default validity: 300 s).

    Args:
        host: Pi-hole hostname or IP address.
        port: Pi-hole HTTP port.
        sid: Session SID to invalidate.
    """
    url = f"http://{host}:{port}/api/auth"
    req = urllib.request.Request(url, method="DELETE")  # nosec B310
    req.add_header("Cookie", f"sid={sid}")
    try:
        with urllib.request.urlopen(req, timeout=5) as _:  # nosec B310
            pass
        logger.debug("Pi-hole session deleted")
    except Exception as e:
        logger.debug(f"Failed to delete Pi-hole session (non-critical): {e}")


def _api_get(host: str, port: int, path: str, sid: str | None = None) -> dict | list:
    """
    Perform an authenticated GET request to the Pi-hole v6 API (BLOCKING).

    Args:
        host: Pi-hole hostname or IP address.
        port: Pi-hole HTTP port.
        path: URL path including any query string (e.g. ``/api/dns/blocking``).
        sid: Optional session SID for authenticated endpoints.

    Returns:
        Parsed JSON response (dict or list depending on the endpoint).

    Raises:
        urllib.error.HTTPError: On 4xx/5xx responses.
        urllib.error.URLError: If the connection fails or times out.
        ValueError: If the response body is not valid JSON.
    """
    url = f"http://{host}:{port}{path}"
    logger.debug(f"Pi-hole API GET: {url}")
    req = urllib.request.Request(url)  # nosec B310
    if sid:
        req.add_header("Cookie", f"sid={sid}")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # nosec B310
            body = resp.read().decode()
    except urllib.error.URLError:
        raise
    try:
        return json.loads(body)
    except json.JSONDecodeError as e:
        raise ValueError(f"Pi-hole API returned invalid JSON: {e}") from e


def _api_post(host: str, port: int, path: str, payload: dict, sid: str) -> dict | list:
    """
    Perform an authenticated POST request to the Pi-hole v6 API (BLOCKING).

    Args:
        host: Pi-hole hostname or IP address.
        port: Pi-hole HTTP port.
        path: URL path (e.g. ``/api/dns/blocking``).
        payload: Dict to serialize as the JSON request body.
        sid: Session SID (required for write operations).

    Returns:
        Parsed JSON response.

    Raises:
        urllib.error.HTTPError: On 4xx/5xx responses.
        urllib.error.URLError: If the connection fails or times out.
        ValueError: If the response body is not valid JSON.
    """
    url = f"http://{host}:{port}{path}"
    logger.debug(f"Pi-hole API POST: {url}")
    body = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=body, method="POST")  # nosec B310
    req.add_header("Content-Type", "application/json")
    req.add_header("Cookie", f"sid={sid}")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # nosec B310
            return json.loads(resp.read().decode())
    except urllib.error.URLError:
        raise
    except json.JSONDecodeError as e:
        raise ValueError(f"Pi-hole API returned invalid JSON: {e}") from e


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


def get_pihole_status(
    host: str = _DEFAULT_HOST,
    port: int = _DEFAULT_PORT,
    password: str | None = None,
) -> PiholeStatus:
    """
    Retrieve Pi-hole blocking state and today's query summary (BLOCKING).

    Fetches ``GET /api/dns/blocking`` for the enabled/disabled state and
    ``GET /api/stats/summary`` for query counts (requires authentication).
    If no password is provided the blocking state is still returned but
    query counts default to zero.

    Args:
        host: Pi-hole hostname or IP address.
        port: Pi-hole HTTP port.
        password: Web admin password. Optional — omit for blocking state only.

    Returns:
        PiholeStatus dataclass.

    Raises:
        urllib.error.HTTPError: On authentication failure or API error.
        urllib.error.URLError: If the Pi-hole API is unreachable.
        ValueError: If the API response is malformed.
    """
    sid = None
    try:
        if password:
            sid = _authenticate(host, port, password)

        blocking_data = _api_get(host, port, "/api/dns/blocking", sid)
        if not isinstance(blocking_data, dict):
            raise ValueError(f"Unexpected /api/dns/blocking response: {blocking_data}")
        enabled = blocking_data.get("blocking") == "enabled"

        total_queries = 0
        blocked_queries = 0
        blocked_percent = 0.0
        domains_blocked = 0

        if sid:
            summary = _api_get(host, port, "/api/stats/summary", sid)
            if not isinstance(summary, dict):
                raise ValueError(f"Unexpected /api/stats/summary response: {summary}")
            queries = summary.get("queries", {})
            gravity = summary.get("gravity", {})
            try:
                total_queries = int(queries.get("total", 0))
                blocked_queries = int(queries.get("blocked", 0))
                blocked_percent = float(queries.get("percent_blocked", 0.0))
                domains_blocked = int(gravity.get("domains_being_blocked", 0))
            except (TypeError, ValueError) as e:
                raise ValueError(f"Malformed Pi-hole summary response: {e}") from e

        return PiholeStatus(
            enabled=enabled,
            total_queries=total_queries,
            blocked_queries=blocked_queries,
            blocked_percent=blocked_percent,
            domains_blocked=domains_blocked,
        )
    finally:
        if sid:
            _delete_session(host, port, sid)


async def get_pihole_status_async(
    host: str = _DEFAULT_HOST,
    port: int = _DEFAULT_PORT,
    password: str | None = None,
) -> PiholeStatus:
    """
    Retrieve Pi-hole status asynchronously.

    Args:
        host: Pi-hole hostname or IP address.
        port: Pi-hole HTTP port.
        password: Web admin password. Optional — omit for blocking state only.

    Returns:
        PiholeStatus dataclass.

    Raises:
        urllib.error.HTTPError: On authentication failure or API error.
        urllib.error.URLError: If the Pi-hole API is unreachable.
        ValueError: If the API response is malformed.
    """
    return await run_blocking(get_pihole_status, host, port, password)


def enable_pihole(host: str, port: int, password: str) -> None:
    """
    Enable Pi-hole ad blocking via ``POST /api/dns/blocking`` (BLOCKING).

    Args:
        host: Pi-hole hostname or IP address.
        port: Pi-hole HTTP port.
        password: Web admin password.

    Raises:
        urllib.error.HTTPError: On authentication failure or API error.
        urllib.error.URLError: If the Pi-hole API is unreachable.
        ValueError: If the API response does not confirm the enabled state.
    """
    sid = _authenticate(host, port, password)
    try:
        data = _api_post(host, port, "/api/dns/blocking", {"blocking": True}, sid)
        if not isinstance(data, dict) or data.get("blocking") != "enabled":
            raise ValueError(f"Unexpected enable response: {data}")
        logger.info("Pi-hole ad blocking enabled")
    finally:
        _delete_session(host, port, sid)


async def enable_pihole_async(host: str, port: int, password: str) -> None:
    """
    Enable Pi-hole ad blocking asynchronously.

    Args:
        host: Pi-hole hostname or IP address.
        port: Pi-hole HTTP port.
        password: Web admin password.

    Raises:
        urllib.error.HTTPError: On authentication failure or API error.
        urllib.error.URLError: If the Pi-hole API is unreachable.
        ValueError: If the API response does not confirm the enabled state.
    """
    await run_blocking(enable_pihole, host, port, password)


def disable_pihole(host: str, port: int, password: str, seconds: int = 0) -> None:
    """
    Disable Pi-hole ad blocking via ``POST /api/dns/blocking`` (BLOCKING).

    Args:
        host: Pi-hole hostname or IP address.
        port: Pi-hole HTTP port.
        password: Web admin password.
        seconds: Duration in seconds; ``0`` (default) means indefinitely.

    Raises:
        urllib.error.HTTPError: On authentication failure or API error.
        urllib.error.URLError: If the Pi-hole API is unreachable.
        ValueError: If the API response does not confirm the disabled state.
    """
    sid = _authenticate(host, port, password)
    try:
        # Pi-hole v6 uses timer=null for indefinite, timer=N for N seconds
        timer: int | None = seconds if seconds > 0 else None
        data = _api_post(
            host, port, "/api/dns/blocking", {"blocking": False, "timer": timer}, sid
        )
        if not isinstance(data, dict) or data.get("blocking") != "disabled":
            raise ValueError(f"Unexpected disable response: {data}")
        duration = f"{seconds}s" if seconds > 0 else "indefinitely"
        logger.info(f"Pi-hole ad blocking disabled ({duration})")
    finally:
        _delete_session(host, port, sid)


async def disable_pihole_async(
    host: str, port: int, password: str, seconds: int = 0
) -> None:
    """
    Disable Pi-hole ad blocking asynchronously.

    Args:
        host: Pi-hole hostname or IP address.
        port: Pi-hole HTTP port.
        password: Web admin password.
        seconds: Duration in seconds; ``0`` means indefinitely.

    Raises:
        urllib.error.HTTPError: On authentication failure or API error.
        urllib.error.URLError: If the Pi-hole API is unreachable.
        ValueError: If the API response does not confirm the disabled state.
    """
    await run_blocking(disable_pihole, host, port, password, seconds)


def get_pihole_top(
    host: str, port: int, password: str, n: int = _DEFAULT_TOP_N
) -> PiholeTopData:
    """
    Retrieve the top queried and top blocked domains from Pi-hole (BLOCKING).

    Calls ``GET /api/stats/top_domains?count=N`` for top allowed queries and
    ``GET /api/stats/top_blocked?count=N`` for top blocked domains.

    Args:
        host: Pi-hole hostname or IP address.
        port: Pi-hole HTTP port.
        password: Web admin password.
        n: Number of top entries per category (default 5).

    Returns:
        PiholeTopData with ``top_queries`` and ``top_ads`` dicts (domain → count).

    Raises:
        urllib.error.HTTPError: On authentication failure or API error.
        urllib.error.URLError: If the Pi-hole API is unreachable.
        ValueError: If the response cannot be parsed.
    """
    sid = _authenticate(host, port, password)
    try:
        queries_data = _api_get(host, port, f"/api/stats/top_domains?count={n}", sid)
        blocked_data = _api_get(host, port, f"/api/stats/top_blocked?count={n}", sid)

        top_queries: dict[str, int] = {}
        for entry in _iter_top_entries(queries_data, ("top_queries", "domains")):
            domain = entry.get("domain") or entry.get("name", "")
            if domain:
                top_queries[domain] = int(entry.get("count", 0))

        top_ads: dict[str, int] = {}
        for entry in _iter_top_entries(blocked_data, ("top_blocked", "domains")):
            domain = entry.get("domain") or entry.get("name", "")
            if domain:
                top_ads[domain] = int(entry.get("count", 0))

        return PiholeTopData(top_queries=top_queries, top_ads=top_ads)
    finally:
        _delete_session(host, port, sid)


def _iter_top_entries(data: dict | list, keys: tuple[str, ...]):
    """
    Extract a list of domain-count entries from a Pi-hole top-domains response.

    Tries each key in ``keys`` in order, returning the first list found.
    If ``data`` is itself a list it is returned directly. Falls back to an
    empty list so callers always get an iterable.

    Args:
        data: Parsed JSON response from a top-domains endpoint.
        keys: Candidate dict keys to look for the list under.

    Returns:
        Iterable of entry dicts (each with ``domain``/``name`` and ``count``).
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in keys:
            value = data.get(key)
            if isinstance(value, list):
                return value
    return []


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
        urllib.error.HTTPError: On authentication failure or API error.
        urllib.error.URLError: If the Pi-hole API is unreachable.
        ValueError: If the response cannot be parsed.
    """
    return await run_blocking(get_pihole_top, host, port, password, n)
