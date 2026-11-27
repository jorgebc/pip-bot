"""Tests for the Kodi systemd service wrapper."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from services.kodi import control_kodi_service, control_kodi_service_async


class TestControlKodiService:
    """Tests for allowlisted Kodi systemd actions."""

    @pytest.mark.parametrize("action", ["start", "stop", "restart"])
    @patch("services.kodi.subprocess.run")
    def test_control_action_uses_fixed_argument_list(self, mock_run, action):
        """Mutating actions use sudo and the fixed systemctl path without a shell."""
        mock_run.return_value = MagicMock(returncode=0, stdout="")

        control_kodi_service(action)

        mock_run.assert_called_once_with(
            ["sudo", "/usr/bin/systemctl", action, "kodi"],
            check=True,
            capture_output=True,
            text=True,
            shell=False,
            timeout=10,
        )

    @patch("services.kodi.subprocess.run")
    def test_invalid_action_is_rejected_before_execution(self, mock_run):
        """An action outside the allowlist never reaches subprocess."""
        with pytest.raises(ValueError, match="Unsupported Kodi action"):
            control_kodi_service("start; reboot")

        mock_run.assert_not_called()

    @pytest.mark.parametrize(
        ("state", "returncode", "expected"),
        [("active", 0, "activo"), ("inactive", 3, "parado"), ("failed", 3, "parado")],
    )
    @patch("services.kodi.subprocess.run")
    def test_status_translates_systemd_state(self, mock_run, state, returncode, expected):
        """Known active and inactive systemd states have readable Spanish results."""
        mock_run.return_value = MagicMock(
            returncode=returncode,
            stdout=f"{state}\n",
            stderr="",
        )

        assert control_kodi_service("status") == expected
        mock_run.assert_called_once_with(
            ["sudo", "/usr/bin/systemctl", "is-active", "kodi"],
            check=False,
            capture_output=True,
            text=True,
            shell=False,
            timeout=10,
        )

    @patch("services.kodi.subprocess.run")
    def test_operation_failure_is_propagated(self, mock_run):
        """A non-zero mutation action is surfaced as CalledProcessError."""
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["sudo", "/usr/bin/systemctl", "restart", "kodi"],
            stderr="permission denied",
        )

        with pytest.raises(subprocess.CalledProcessError):
            control_kodi_service("restart")

    @patch("services.kodi.subprocess.run")
    def test_missing_systemctl_is_propagated(self, mock_run):
        """Missing systemctl is reported explicitly."""
        mock_run.side_effect = FileNotFoundError("systemctl not found")

        with pytest.raises(FileNotFoundError):
            control_kodi_service("start")

    @patch("services.kodi.subprocess.run")
    def test_timeout_is_propagated(self, mock_run):
        """A hanging systemctl call is bounded by the subprocess timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="systemctl", timeout=10)

        with pytest.raises(subprocess.TimeoutExpired):
            control_kodi_service("stop")

    @patch("services.kodi.subprocess.run")
    def test_unknown_status_is_reported_as_error(self, mock_run):
        """Unexpected is-active output is not presented as a stopped service."""
        mock_run.return_value = MagicMock(returncode=4, stdout="unknown\n", stderr="")

        with pytest.raises(RuntimeError, match="unexpected Kodi service state"):
            control_kodi_service("status")


class TestControlKodiServiceAsync:
    """Tests for the non-blocking wrapper."""

    @patch("services.kodi.subprocess.run")
    @pytest.mark.asyncio
    async def test_async_wrapper_runs_status(self, mock_run):
        """The async wrapper delegates the status action and returns its result."""
        mock_run.return_value = MagicMock(returncode=0, stdout="active\n", stderr="")

        assert await control_kodi_service_async("status") == "activo"
