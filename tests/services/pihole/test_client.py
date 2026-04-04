"""Tests for services/pihole/client.py."""

import hashlib
import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from services.pihole.client import (
    PiholeStatus,
    PiholeTopData,
    _compute_auth,
    disable_pihole,
    enable_pihole,
    get_pihole_status,
    get_pihole_top,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_urlopen(payload: dict | list):
    """Return a context-manager mock that yields a readable response body."""
    body = json.dumps(payload).encode()
    mock_response = MagicMock()
    mock_response.read.return_value = body
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


# ---------------------------------------------------------------------------
# _compute_auth
# ---------------------------------------------------------------------------

class TestComputeAuth:
    """Tests for the _compute_auth helper."""

    def test_returns_double_md5(self):
        """Result must be the double-MD5 hex digest of the input."""
        password = "admin"
        first = hashlib.md5(password.encode()).hexdigest()
        expected = hashlib.md5(first.encode()).hexdigest()
        assert _compute_auth(password) == expected

    def test_empty_password(self):
        """Empty password should still produce a valid hex digest."""
        result = _compute_auth("")
        assert len(result) == 32
        assert all(c in "0123456789abcdef" for c in result)

    def test_deterministic(self):
        """Same password always produces the same token."""
        assert _compute_auth("secret") == _compute_auth("secret")


# ---------------------------------------------------------------------------
# get_pihole_status
# ---------------------------------------------------------------------------

class TestGetPiholeStatus:
    """Tests for get_pihole_status."""

    def test_returns_enabled_status(self):
        """Happy path: returns PiholeStatus with parsed values."""
        payload = {
            "status": "enabled",
            "dns_queries_today": 1500,
            "ads_blocked_today": 300,
            "ads_percentage_today": 20.0,
            "domains_being_blocked": 100000,
        }
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(payload)):
            result = get_pihole_status()

        assert isinstance(result, PiholeStatus)
        assert result.enabled is True
        assert result.total_queries == 1500
        assert result.blocked_queries == 300
        assert result.blocked_percent == 20.0
        assert result.domains_blocked == 100000

    def test_returns_disabled_status(self):
        """Disabled Pi-hole sets enabled=False."""
        payload = {
            "status": "disabled",
            "dns_queries_today": 0,
            "ads_blocked_today": 0,
            "ads_percentage_today": 0.0,
            "domains_being_blocked": 50000,
        }
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(payload)):
            result = get_pihole_status()

        assert result.enabled is False

    def test_raises_on_url_error(self):
        """URLError (unreachable host) propagates to caller."""
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("Connection refused"),
        ):
            with pytest.raises(urllib.error.URLError):
                get_pihole_status()

    def test_raises_on_invalid_json(self):
        """Non-JSON response raises ValueError."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"not json"
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock_response):
            with pytest.raises(ValueError, match="invalid JSON"):
                get_pihole_status()

    def test_raises_on_list_response(self):
        """A list response (should never happen for summary) raises ValueError."""
        with patch("urllib.request.urlopen", return_value=_mock_urlopen([])):
            with pytest.raises(ValueError):
                get_pihole_status()

    def test_missing_fields_default_to_zero(self):
        """Missing numeric fields default to zero rather than raising."""
        payload = {"status": "enabled"}
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(payload)):
            result = get_pihole_status()

        assert result.total_queries == 0
        assert result.blocked_queries == 0
        assert result.blocked_percent == 0.0
        assert result.domains_blocked == 0


# ---------------------------------------------------------------------------
# enable_pihole
# ---------------------------------------------------------------------------

class TestEnablePihole:
    """Tests for enable_pihole."""

    def test_enable_succeeds(self):
        """Happy path: no exception when Pi-hole confirms enabled."""
        payload = {"status": "enabled"}
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(payload)):
            enable_pihole("localhost", 80, "admin")  # should not raise

    def test_raises_on_wrong_status(self):
        """ValueError raised if Pi-hole does not return enabled status."""
        payload = {"status": "disabled"}
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(payload)):
            with pytest.raises(ValueError, match="expected status"):
                enable_pihole("localhost", 80, "admin")

    def test_raises_on_url_error(self):
        """URLError propagates when Pi-hole is unreachable."""
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("refused"),
        ):
            with pytest.raises(urllib.error.URLError):
                enable_pihole("localhost", 80, "admin")


# ---------------------------------------------------------------------------
# disable_pihole
# ---------------------------------------------------------------------------

class TestDisablePihole:
    """Tests for disable_pihole."""

    def test_disable_indefinite(self):
        """Happy path: disable indefinitely (seconds=0)."""
        payload = {"status": "disabled"}
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(payload)):
            disable_pihole("localhost", 80, "admin", 0)  # should not raise

    def test_disable_for_duration(self):
        """Disable for a fixed duration passes seconds in query string."""
        payload = {"status": "disabled"}
        captured_url: list[str] = []

        def fake_urlopen(url, timeout=10):
            captured_url.append(url)
            return _mock_urlopen(payload)

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            disable_pihole("localhost", 80, "admin", 300)

        assert "disable=300" in captured_url[0]

    def test_raises_on_wrong_status(self):
        """ValueError raised if Pi-hole does not return disabled status."""
        payload = {"status": "enabled"}
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(payload)):
            with pytest.raises(ValueError, match="expected status"):
                disable_pihole("localhost", 80, "admin", 0)

    def test_raises_on_url_error(self):
        """URLError propagates when Pi-hole is unreachable."""
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("refused"),
        ):
            with pytest.raises(urllib.error.URLError):
                disable_pihole("localhost", 80, "admin")


# ---------------------------------------------------------------------------
# get_pihole_top
# ---------------------------------------------------------------------------

class TestGetPiholeTop:
    """Tests for get_pihole_top."""

    def test_returns_top_data(self):
        """Happy path: returns PiholeTopData with parsed dicts."""
        payload = {
            "top_queries": {"example.com": 100, "google.com": 80},
            "top_ads": {"ad.com": 30, "tracker.io": 10},
        }
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(payload)):
            result = get_pihole_top("localhost", 80, "admin")

        assert isinstance(result, PiholeTopData)
        assert result.top_queries == {"example.com": 100, "google.com": 80}
        assert result.top_ads == {"ad.com": 30, "tracker.io": 10}

    def test_raises_on_list_response(self):
        """Pi-hole returns [] when privacy level is too high — raises ValueError."""
        with patch("urllib.request.urlopen", return_value=_mock_urlopen([])):
            with pytest.raises(ValueError, match="privacy level"):
                get_pihole_top("localhost", 80, "admin")

    def test_empty_top_queries_and_ads(self):
        """Missing keys default to empty dicts."""
        payload = {}
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(payload)):
            result = get_pihole_top("localhost", 80, "admin")

        assert result.top_queries == {}
        assert result.top_ads == {}

    def test_query_includes_top_n(self):
        """The API request should include the topItems parameter."""
        payload = {"top_queries": {}, "top_ads": {}}
        captured_url: list[str] = []

        def fake_urlopen(url, timeout=10):
            captured_url.append(url)
            return _mock_urlopen(payload)

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            get_pihole_top("localhost", 80, "admin", n=10)

        assert "topItems=10" in captured_url[0]

    def test_raises_on_url_error(self):
        """URLError propagates when Pi-hole is unreachable."""
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("refused"),
        ):
            with pytest.raises(urllib.error.URLError):
                get_pihole_top("localhost", 80, "admin")


# ---------------------------------------------------------------------------
# Async wrappers
# ---------------------------------------------------------------------------

class TestAsyncWrappers:
    """Verify async wrappers delegate to synchronous counterparts."""

    @pytest.mark.asyncio
    async def test_get_pihole_status_async(self):
        """get_pihole_status_async should delegate to get_pihole_status."""
        payload = {
            "status": "enabled",
            "dns_queries_today": 500,
            "ads_blocked_today": 50,
            "ads_percentage_today": 10.0,
            "domains_being_blocked": 75000,
        }
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(payload)):
            from services.pihole.client import get_pihole_status_async

            result = await get_pihole_status_async()
        assert result.enabled is True
        assert result.total_queries == 500

    @pytest.mark.asyncio
    async def test_enable_pihole_async(self):
        """enable_pihole_async should delegate to enable_pihole."""
        payload = {"status": "enabled"}
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(payload)):
            from services.pihole.client import enable_pihole_async

            await enable_pihole_async("localhost", 80, "admin")  # no raise

    @pytest.mark.asyncio
    async def test_disable_pihole_async(self):
        """disable_pihole_async should delegate to disable_pihole."""
        payload = {"status": "disabled"}
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(payload)):
            from services.pihole.client import disable_pihole_async

            await disable_pihole_async("localhost", 80, "admin", 60)  # no raise

    @pytest.mark.asyncio
    async def test_get_pihole_top_async(self):
        """get_pihole_top_async should delegate to get_pihole_top."""
        payload = {"top_queries": {"a.com": 5}, "top_ads": {"b.com": 2}}
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(payload)):
            from services.pihole.client import get_pihole_top_async

            result = await get_pihole_top_async("localhost", 80, "admin")
        assert result.top_queries == {"a.com": 5}
