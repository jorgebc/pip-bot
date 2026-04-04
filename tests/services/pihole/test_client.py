"""Tests for services/pihole/client.py (Pi-hole v6 REST API)."""

import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from services.pihole.client import (
    PiholeStatus,
    PiholeTopData,
    _authenticate,
    _delete_session,
    _iter_top_entries,
    disable_pihole,
    enable_pihole,
    get_pihole_status,
    get_pihole_top,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_response(payload: dict | list, status: int = 200):
    """Return a context-manager mock that yields a readable HTTP response."""
    body = json.dumps(payload).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.status = status
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def _http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(url="", code=code, msg="", hdrs=None, fp=None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# _authenticate
# ---------------------------------------------------------------------------


class TestAuthenticate:
    """Tests for _authenticate."""

    def test_returns_sid_on_success(self):
        """Happy path: extracts SID from successful auth response."""
        payload = {"session": {"sid": "abc123", "valid": True}}
        with patch("urllib.request.urlopen", return_value=_mock_response(payload)):
            sid = _authenticate("localhost", 80, "admin")
        assert sid == "abc123"

    def test_raises_value_error_when_sid_missing(self):
        """Raises ValueError if response does not contain a SID."""
        payload = {"session": {}}
        with patch("urllib.request.urlopen", return_value=_mock_response(payload)):
            with pytest.raises(ValueError, match="missing SID"):
                _authenticate("localhost", 80, "admin")

    def test_raises_http_error_on_401(self):
        """Propagates HTTPError when credentials are rejected."""
        with patch("urllib.request.urlopen", side_effect=_http_error(401)):
            with pytest.raises(urllib.error.HTTPError) as exc_info:
                _authenticate("localhost", 80, "wrong")
        assert exc_info.value.code == 401

    def test_raises_url_error_on_connection_failure(self):
        """Propagates URLError when Pi-hole is unreachable."""
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("refused"),
        ):
            with pytest.raises(urllib.error.URLError):
                _authenticate("localhost", 80, "admin")


# ---------------------------------------------------------------------------
# _delete_session
# ---------------------------------------------------------------------------


class TestDeleteSession:
    """Tests for _delete_session."""

    def test_sends_delete_request(self):
        """Sends a DELETE request with the SID as a query parameter."""
        with patch("urllib.request.urlopen", return_value=_mock_response({})) as mock_open:
            _delete_session("localhost", 80, "abc123")
        req = mock_open.call_args[0][0]
        assert req.get_method() == "DELETE"
        assert "sid=abc123" in req.full_url

    def test_swallows_errors(self):
        """Errors during session deletion do not propagate."""
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("refused"),
        ):
            _delete_session("localhost", 80, "abc123")  # must not raise


# ---------------------------------------------------------------------------
# get_pihole_status
# ---------------------------------------------------------------------------


class TestGetPiholeStatus:
    """Tests for get_pihole_status."""

    def _setup_mocks(self, blocking_payload, summary_payload=None):
        """Return a side_effect list for urlopen covering auth, API calls, logout."""
        auth_resp = _mock_response({"session": {"sid": "sid1"}})
        blocking_resp = _mock_response(blocking_payload)
        delete_resp = _mock_response({})
        if summary_payload is not None:
            summary_resp = _mock_response(summary_payload)
            return [auth_resp, blocking_resp, summary_resp, delete_resp]
        return [auth_resp, blocking_resp, delete_resp]

    def test_returns_full_status_with_password(self):
        """With password: returns enabled state and full query stats."""
        blocking = {"blocking": "enabled"}
        summary = {
            "queries": {"total": 1000, "blocked": 100, "percent_blocked": 10.0},
            "gravity": {"domains_being_blocked": 50000},
        }
        with patch(
            "urllib.request.urlopen",
            side_effect=self._setup_mocks(blocking, summary),
        ):
            result = get_pihole_status("localhost", 80, "admin")

        assert isinstance(result, PiholeStatus)
        assert result.enabled is True
        assert result.total_queries == 1000
        assert result.blocked_queries == 100
        assert result.blocked_percent == 10.0
        assert result.domains_blocked == 50000

    def test_returns_blocking_state_without_password(self):
        """Without password: returns enabled state; stats default to zero."""
        blocking = {"blocking": "disabled"}
        with patch(
            "urllib.request.urlopen",
            return_value=_mock_response(blocking),
        ):
            result = get_pihole_status("localhost", 80, password=None)

        assert result.enabled is False
        assert result.total_queries == 0
        assert result.blocked_queries == 0

    def test_deletes_session_on_success(self):
        """Session is always cleaned up after a successful call."""
        blocking = {"blocking": "enabled"}
        summary = {"queries": {}, "gravity": {}}
        calls: list = []

        def fake_urlopen(req, timeout=10):
            calls.append(req)
            if len(calls) == 1:
                return _mock_response({"session": {"sid": "s1"}})
            if len(calls) == 2:
                return _mock_response(blocking)
            if len(calls) == 3:
                return _mock_response(summary)
            return _mock_response({})  # delete

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            get_pihole_status("localhost", 80, "admin")

        # Last request should be the DELETE
        assert calls[-1].get_method() == "DELETE"

    def test_deletes_session_on_api_error(self):
        """Session is cleaned up even when an API call raises."""
        delete_calls: list = []

        def fake_urlopen(req, timeout=10):
            if req.get_method() == "DELETE":
                delete_calls.append(req)
                return _mock_response({})
            if b"password" in (req.data or b""):
                return _mock_response({"session": {"sid": "s1"}})
            raise urllib.error.URLError("boom")

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            with pytest.raises(urllib.error.URLError):
                get_pihole_status("localhost", 80, "admin")

        assert len(delete_calls) == 1

    def test_raises_on_malformed_blocking_response(self):
        """ValueError raised if /api/dns/blocking returns a list."""
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = [
                _mock_response({"session": {"sid": "s1"}}),
                _mock_response([]),  # list instead of dict
                _mock_response({}),  # delete
            ]
            with pytest.raises(ValueError):
                get_pihole_status("localhost", 80, "admin")


# ---------------------------------------------------------------------------
# enable_pihole
# ---------------------------------------------------------------------------


class TestEnablePihole:
    """Tests for enable_pihole."""

    def test_enable_succeeds(self):
        """Happy path: no exception when Pi-hole confirms enabled."""
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = [
                _mock_response({"session": {"sid": "s1"}}),
                _mock_response({"blocking": "enabled"}),
                _mock_response({}),  # delete
            ]
            enable_pihole("localhost", 80, "admin")  # must not raise

    def test_raises_on_wrong_status(self):
        """ValueError raised when response does not confirm enabled."""
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = [
                _mock_response({"session": {"sid": "s1"}}),
                _mock_response({"blocking": "disabled"}),
                _mock_response({}),
            ]
            with pytest.raises(ValueError, match="Unexpected enable"):
                enable_pihole("localhost", 80, "admin")

    def test_raises_http_error_on_auth_failure(self):
        """HTTPError propagates when authentication is rejected."""
        with patch("urllib.request.urlopen", side_effect=_http_error(401)):
            with pytest.raises(urllib.error.HTTPError):
                enable_pihole("localhost", 80, "wrong")


# ---------------------------------------------------------------------------
# disable_pihole
# ---------------------------------------------------------------------------


class TestDisablePihole:
    """Tests for disable_pihole."""

    def test_disable_indefinite(self):
        """Happy path: disable with seconds=0 sends timer=null."""
        captured: list = []

        def fake_urlopen(req, timeout=10):
            captured.append(req)
            if b"password" in (req.data or b""):
                return _mock_response({"session": {"sid": "s1"}})
            if req.data:
                return _mock_response({"blocking": "disabled"})
            return _mock_response({})  # delete

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            disable_pihole("localhost", 80, "admin", 0)

        # Find the POST to /api/dns/blocking
        post_req = next(r for r in captured if r.data and b"blocking" in r.data)
        body = json.loads(post_req.data)
        assert body["blocking"] is False
        assert body["timer"] is None

    def test_disable_for_duration_sends_timer(self):
        """Disable for N seconds sends timer=N in the request body."""
        captured: list = []

        def fake_urlopen(req, timeout=10):
            captured.append(req)
            if b"password" in (req.data or b""):
                return _mock_response({"session": {"sid": "s1"}})
            if req.data:
                return _mock_response({"blocking": "disabled"})
            return _mock_response({})

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            disable_pihole("localhost", 80, "admin", 300)

        post_req = next(r for r in captured if r.data and b"blocking" in r.data)
        body = json.loads(post_req.data)
        assert body["timer"] == 300

    def test_raises_on_wrong_status(self):
        """ValueError raised when response does not confirm disabled."""
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = [
                _mock_response({"session": {"sid": "s1"}}),
                _mock_response({"blocking": "enabled"}),
                _mock_response({}),
            ]
            with pytest.raises(ValueError, match="Unexpected disable"):
                disable_pihole("localhost", 80, "admin")


# ---------------------------------------------------------------------------
# get_pihole_top
# ---------------------------------------------------------------------------


class TestGetPiholeTop:
    """Tests for get_pihole_top."""

    def test_returns_top_data(self):
        """Happy path: parses top_queries and top_blocked into dicts."""
        top_domains_resp = {
            "top_queries": [
                {"domain": "example.com", "count": 100},
                {"domain": "google.com", "count": 80},
            ]
        }
        top_blocked_resp = {
            "top_blocked": [
                {"domain": "ad.com", "count": 30},
            ]
        }
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = [
                _mock_response({"session": {"sid": "s1"}}),
                _mock_response(top_domains_resp),
                _mock_response(top_blocked_resp),
                _mock_response({}),  # delete
            ]
            result = get_pihole_top("localhost", 80, "admin")

        assert isinstance(result, PiholeTopData)
        assert result.top_queries == {"example.com": 100, "google.com": 80}
        assert result.top_ads == {"ad.com": 30}

    def test_empty_results_yield_empty_dicts(self):
        """Empty lists from the API produce empty dicts in PiholeTopData."""
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = [
                _mock_response({"session": {"sid": "s1"}}),
                _mock_response({}),
                _mock_response({}),
                _mock_response({}),
            ]
            result = get_pihole_top("localhost", 80, "admin")

        assert result.top_queries == {}
        assert result.top_ads == {}

    def test_query_includes_count_param(self):
        """API requests include the ?count=N parameter."""
        captured: list = []

        def fake_urlopen(req, timeout=10):
            captured.append(req.full_url)
            if b"password" in (req.data or b""):
                return _mock_response({"session": {"sid": "s1"}})
            return _mock_response({})

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            get_pihole_top("localhost", 80, "admin", n=10)

        assert any("count=10" in url for url in captured)

    def test_raises_http_error_on_auth_failure(self):
        """HTTPError propagates when authentication is rejected."""
        with patch("urllib.request.urlopen", side_effect=_http_error(401)):
            with pytest.raises(urllib.error.HTTPError):
                get_pihole_top("localhost", 80, "wrong")


# ---------------------------------------------------------------------------
# _iter_top_entries
# ---------------------------------------------------------------------------


class TestIterTopEntries:
    """Tests for the _iter_top_entries helper."""

    def test_extracts_list_by_first_matching_key(self):
        data = {"top_queries": [{"domain": "a.com", "count": 1}]}
        result = list(_iter_top_entries(data, ("top_queries", "domains")))
        assert result == [{"domain": "a.com", "count": 1}]

    def test_falls_back_to_second_key(self):
        data = {"domains": [{"domain": "b.com", "count": 2}]}
        result = list(_iter_top_entries(data, ("top_queries", "domains")))
        assert result == [{"domain": "b.com", "count": 2}]

    def test_returns_list_directly_when_data_is_list(self):
        data = [{"domain": "c.com", "count": 3}]
        result = list(_iter_top_entries(data, ("top_queries",)))
        assert result == data

    def test_returns_empty_when_no_key_matches(self):
        result = list(_iter_top_entries({}, ("top_queries",)))
        assert result == []


# ---------------------------------------------------------------------------
# Async wrappers
# ---------------------------------------------------------------------------


class TestAsyncWrappers:
    """Verify async wrappers delegate to the synchronous counterparts."""

    @pytest.mark.asyncio
    async def test_get_pihole_status_async(self):
        blocking = {"blocking": "enabled"}
        summary = {
            "queries": {"total": 500, "blocked": 50, "percent_blocked": 10.0},
            "gravity": {"domains_being_blocked": 75000},
        }
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = [
                _mock_response({"session": {"sid": "s1"}}),
                _mock_response(blocking),
                _mock_response(summary),
                _mock_response({}),
            ]
            from services.pihole.client import get_pihole_status_async

            result = await get_pihole_status_async("localhost", 80, "admin")
        assert result.enabled is True
        assert result.total_queries == 500

    @pytest.mark.asyncio
    async def test_enable_pihole_async(self):
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = [
                _mock_response({"session": {"sid": "s1"}}),
                _mock_response({"blocking": "enabled"}),
                _mock_response({}),
            ]
            from services.pihole.client import enable_pihole_async

            await enable_pihole_async("localhost", 80, "admin")

    @pytest.mark.asyncio
    async def test_disable_pihole_async(self):
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = [
                _mock_response({"session": {"sid": "s1"}}),
                _mock_response({"blocking": "disabled"}),
                _mock_response({}),
            ]
            from services.pihole.client import disable_pihole_async

            await disable_pihole_async("localhost", 80, "admin", 60)

    @pytest.mark.asyncio
    async def test_get_pihole_top_async(self):
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = [
                _mock_response({"session": {"sid": "s1"}}),
                _mock_response({"top_queries": [{"domain": "a.com", "count": 5}]}),
                _mock_response({"top_blocked": [{"domain": "b.com", "count": 2}]}),
                _mock_response({}),
            ]
            from services.pihole.client import get_pihole_top_async

            result = await get_pihole_top_async("localhost", 80, "admin")
        assert result.top_queries == {"a.com": 5}
        assert result.top_ads == {"b.com": 2}
